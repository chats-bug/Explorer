import datetime
import json
from typing import Literal

import questionary
from questionary import Separator
import os

from lib import logger
from config import console, config
from utils.doc import Doc, DocUtils, get_doc
from agents.ContextCollectorAgent import ContextCollectorAgent
from agents.ExplorationAgent import ExplorationAgent
from agents.PlannerAgent.agent import PlannerAgent
from tools import ListFiles, ReadCode, ReadCodeSnippet, LSPUtils, Finish
from llms import (
    OpenAiLLM,
    OpenAiChatModels,
    OpenAIDecodingArguments,
    AnthropicLLM,
    AnthropicDecodingArguments,
    AnthropicModels,
)


def run_context_collector_agent(root_doc: Doc, user_input: str, directory: str):
    context_collector_agent = ContextCollectorAgent(root_doc=root_doc)
    response = context_collector_agent.run(directory=directory, user_input=user_input)
    return response


def run_exploration_agent(root_doc: Doc, user_prompt: str, directory: str):
    exploration_agent = ExplorationAgent(root_doc=root_doc, title="Exploration Agent")
    response = exploration_agent.run(user_prompt=user_prompt, directory=directory)
    return response


def transform_query_to_exploration_prompt(query: str, directory_overview: str):
    llm = OpenAiLLM(
        model=OpenAiChatModels.GPT_4O, config=config, title="Query to Exploration"
    )
    an_llm = AnthropicLLM(
        model=AnthropicModels.CLAUDE_3_5_SONNET_20240620,
        config=config,
        title="Query to Exploration",
    )
    response = llm.chat(
        messages=[
            {"role": "system", "content": "You are a helpful coding assistant"},
            {
                "role": "user",
                "content": "You will be given a user feature request for a particular code repository. You will "
                "transform this request into a request to explore similar features in the repository.\n"
                "For example, if the user asks for a feature to add a delete button to the 'fill details' "
                "section, you will ask the assistant to explore how delete buttons are implemented in the "
                "other sections of the repository and how other buttons are implemented in the 'fill "
                "details' section\n"
                "Here is the directory overview of the repository:\n"
                f"{directory_overview}\n"
                f"User Feature Request: {query}"
                "Reply only in the following JSON format:"
                """{
                "thought": "What should be an appropriate exploration prompt for the user feature request?",
                "exploration_prompt: "<exploration_prompt>"
                }
                RETURN ONLY THE JSON""",
            },
        ],
        decoding_args=OpenAIDecodingArguments(
            temperature=0.1,
            response_format={"type": "json_object"},
        ),
        # decoding_args=AnthropicDecodingArguments(temperature=0.1),
    )
    response = json.loads(response["content"])
    return response["exploration_prompt"]


def run_planner_agent(
    root_doc: Doc,
    user_prompt: str,
    directory: str,
    exploration_context: dict,
    model_provider: Literal["openai", "anthropic"],
):
    formatted_str = ""
    if exploration_context:
        formatted_str = ""
        formatted_str += f"Explanation:\n{exploration_context.get('explanation')}\n"
        formatted_str += (
            f"Code Flow Graph:\n{exploration_context.get('code_flow_graph')}\n"
        )
        formatted_str += f"Relevant Files:\n"
        read_code = ReadCode(
            root_doc=root_doc, file_path="", start_line=0, end_line=500, max_lines=500
        )
        for f in exploration_context.get("relevant_files"):
            file_name = f.split(":")[0]
            read_code.file_path = file_name
            res = read_code.run()
            formatted_str += f"- {f}\n"
            formatted_str += res["response"]
            formatted_str += "\n" + "-" * 50 + "\n"
        formatted_str += (
            f"Relevant Directories:\n{exploration_context.get('similar_feature_dirs')}"
        )
    planer_agent = PlannerAgent(
        root_doc=root_doc, model_provider=model_provider, title="Planner Agent"
    )
    response = planer_agent.run(
        directory=directory,
        user_prompt=user_prompt,
        exploration_context=formatted_str,
    )
    console.print(f"Final Response: {planer_agent.finish_response}")
    console.print(f"Final Plan: \n{planer_agent.plan}")
    console.print(f"Action graph: \n{json.dumps(planer_agent.action_graph, indent=4)}")
    os.makedirs("saved_states/planner", exist_ok=True)
    with open("saved_states/planner/plan.json", "w") as f:
        f.write(json.dumps(planer_agent.plan, indent=4))
    return response


def main():
    questionary.print("Welcome to the New Context Agent!")
    # root_path = questionary.path("Enter the root path of the project:").ask()
    # root_path = os.path.abspath(root_path)
    root_path = "workspace/SuperAGI"
    with console.status("[bold green] Generating documentation..."):
        root_doc = get_doc(root_path)

    user_input = questionary.text("Enter the feature description:").ask()

    directory = questionary.path(
        "Enter the directory path: (Press enter to search in root)"
    ).ask()
    if not directory:
        directory = root_path

    agent_to_run = questionary.select(
        "Select the agent to run:",
        choices=[
            Separator("---- Agents ----"),
            "Exploration Agent",
            "Context Collector Agent",
            "Planner Agent",
        ],
        pointer="👉",
        use_indicator=True,
        style=questionary.Style([("highlighted", "fg:#FF9D00 bold reverse")]),
    ).ask()
    model_choice = questionary.select(
        "Select the model to use:",
        choices=[
            Separator("---- Models ----"),
            "OpenAI: GPT-4O",
            "Anthropic: Claude 3.5 Sonnet",
        ],
        pointer="👉",
        use_indicator=True,
        style=questionary.Style([("highlighted", "fg:#FF9D00 bold reverse")]),
    ).ask()

    if agent_to_run == "Exploration Agent":
        directory_overview = ListFiles(root_doc=root_doc, directory=directory).run()
        exploration_prompt = transform_query_to_exploration_prompt(
            query=user_input, directory_overview=directory_overview["response"]
        )
        logger.info(f"Exploration Prompt: {exploration_prompt}")
        exploration_agent = ExplorationAgent(
            root_doc=root_doc,
            model_provider="openai" if "OpenAI" in model_choice else "anthropic",
            title="Exploration Agent",
        )
        response = exploration_agent.run(
            user_prompt=exploration_prompt,
            directory=directory,
        )
        exploration_context = exploration_agent.context
        file_path = f"saved_states/exploration/state.json"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(json.dumps(exploration_context, indent=4))
    elif agent_to_run == "Context Collector Agent":
        context_collector_agent = ContextCollectorAgent(root_doc=root_doc)
        response = context_collector_agent.run(
            directory=directory, user_input=user_input
        )
        console.print(response["response"])
    else:
        exp_file_path = "saved_states/exploration/state.json"
        logger.info(f"Reading exploration context {exp_file_path}")
        exploration_context = open(exp_file_path).read()
        exploration_context = json.loads(exploration_context)
        _ = run_planner_agent(
            root_doc=root_doc,
            user_prompt=user_input,
            directory=directory,
            exploration_context=exploration_context,
            model_provider="openai" if "OpenAI" in model_choice else "anthropic",
        )


if __name__ == "__main__":
    main()
