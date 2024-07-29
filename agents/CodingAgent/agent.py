import json
import os
from typing import Literal, Optional, List

from lib import logger
from utils.doc import Doc
from config import config
from agents.base_agent import BaseAgent
from agents.PlannerAgent.tools.update_plan import Task
from llms import OpenAiChatModels, AnthropicModels
from agents.CodingAgent.plan_assimilator import PlanAssimilator
from agents.CodingAgent.code_planner import CodePlanner
from agents.CodingAgent.code_generator import CodeGenerator


class CodingAgent(BaseAgent):
    """
    This agent is not actually an AGENT!
    It just calls a series of smaller "agents" (these are not ReACT agents; simple LLM calls) to do the following:
    - generate plan for file (CodePlanner)
    - assimilate the plan for one consolidated overview (PlanAssimilator)
    - generate code based on the assimilated plan (CodeGenerator)
    """

    def __init__(
        self,
        root_doc: Doc,
        title: str,
        task_id: str,
        max_retries: int = 5,
        model_provider: Literal["openai", "anthropic"] = "openai",
    ):
        if model_provider == "openai":
            model = OpenAiChatModels.GPT_4O
        elif model_provider == "anthropic":
            model = AnthropicModels.CLAUDE_3_5_SONNET_20240620
        else:
            raise ValueError("Invalid model provider")

        super().__init__(
            model=model,
            config=config,
            return_type="json_object",
            max_retries=max_retries,
            title=title,
        )

        self.root_doc = root_doc

        # self.instructions_prompt = open("agents/prompts/planner_prompt.txt").read()
        self.code_planner = CodePlanner(
            model=model,
            config=config,
            title=title,
            max_retries=max_retries,
        )
        self.plan_assimilator = PlanAssimilator(
            model=model,
            config=config,
            title=title,
            max_retries=max_retries,
        )
        self.code_generator = CodeGenerator(
            model=model,
            config=config,
            title=title,
            max_retries=max_retries,
        )

        self.save_dir = f"saved_states/features/{task_id}/code_generator"
        os.makedirs(self.save_dir, exist_ok=True)

    def run(
        self,
        plan: List[Task],
    ):
        for task in plan:
            task_desc = f"DESCRIPTION: {task.task_description}; "
            # if task.create:
            #     task_desc += f"FILES TO CREATE: {task.create}\n---\n"
            if task.update_info:
                task_desc += f"{task.update_info}\n---\n"
            if task.reference:
                task_desc += f"REFERENCE FILES: {task.reference}\nREFERENCE INFO: {task.reference_info}\n---\n"

            # Run the following stuff for individual files
            code_plans = []
            for file_to_edit in task.update:
                logger.info(f"Generating plan for {file_to_edit}: {task_desc}")
                code_plan = self.code_planner.run(
                    user_query=task_desc,
                    file_paths=task.reference + [file_to_edit],
                )
                code_plans.append({"file": file_to_edit, "code_plan": code_plan})
            with open(os.path.join(self.save_dir, "code_plans.json"), "w") as f:
                f.write(json.dumps(code_plans, indent=4))

            logger.info(f"Assimilating plans for {task_desc}")
            assimilated_plan = self.plan_assimilator.run(
                user_query=task_desc,
                plans=[cp["code_plan"] for cp in code_plans],
            )
            with open(os.path.join(self.save_dir, "assimilated_plan.json"), "w") as f:
                f.write(json.dumps(assimilated_plan, indent=4))

            code_gen_responses = []
            for plan in assimilated_plan["plan_of_action"]:
                logger.info(f"Generating code for {plan['file_name']}: {task_desc}")
                code_gen_response = self.code_generator.run(
                    plan["plan"], plan["file_name"]
                )
                code_gen_responses.append(code_gen_response)
            with open(os.path.join(self.save_dir, "code_gen_responses.txt"), "w") as f:
                f.write("\n---\n".join(code_gen_responses))
