import json
from typing import Literal

from agents.base_agent import BaseAgent
from config import config

from utils.doc import Doc
from lib import logger
from tools import ListFiles, ReadCode, ReadCodeSnippet, LSPUtils, Finish
from agents.ExplorationAgent.tools import UpdateContext
from tools.utils import generate_tools_subprompt
from llms import OpenAiChatModels, AnthropicModels
from agents import MaxIterationsReached


class ExplorationAgent(BaseAgent):
    def __init__(
        self,
        root_doc: Doc,
        title: str,
        max_retries: int = 5,
        max_iters: int = 50,
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
            max_iters=max_iters,
            title=title,
        )

        self.root_doc = root_doc

        self.instructions_prompt = open("agents/prompts/exploration_prompt.txt").read()
        self.list_files_tool = ListFiles(root_doc=root_doc, directory="")
        self.tools_dictionary.update(
            {
                "list_files": ListFiles,
                "read_file": ReadCode,
                "read_code_snippet": ReadCodeSnippet,
                # "lsp": LSPUtils,
                "update_context": UpdateContext,
            }
        )
        self.context = {
            "explanation": "",
            "code_flow_graph": "",
            "relevant_files": [],
            "similar_feature_dirs": [],
        }

    def run(self, directory: str, user_prompt: str):
        self.action_graph = []
        self.list_files_tool.directory = directory
        files_list = self.list_files_tool.run()
        if files_list["success"]:
            files_list = files_list["response"]
        else:
            raise Exception("Failed to list files")
        instructions_prompt = self.instructions_prompt.format(
            INITIAL_REPO_MAP=files_list,
            AVAILABLE_TOOLS=generate_tools_subprompt(self.tools_dictionary),
            USER_REQUEST=user_prompt,
            CONTEXT_UPDATE_TOOL_NAME="update_context",
        )
        system_prompt = (
            "You are an AI assistant tasked with exploring a code repository and providing insights based "
            "on a user's request."
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": instructions_prompt},
        ]

        logger.debug(f"System Prompt: {system_prompt}")
        logger.debug(f"User Prompt: {instructions_prompt}")

        num_iters = 0
        while num_iters < self.max_iters:
            messages.append(
                {
                    "role": "user",
                    "content": f"## Current Context: \n {json.dumps(self.context, indent=2)}",
                }
            )
            try:
                unparsed_response, response = self.get_llm_response(
                    messages=messages, parse_response=True
                )
            except Exception as e:
                raise e

            logger.debug(
                f"[bold bright_white on #C738BD]   🧠 Thought   [/]  \n{response['thought']}\n"
            )

            observation, finish_loop = self.run_tool(
                tool_name=response.get("tool"),
                tool_args=response.get("tool_args"),
                extra_args={
                    "root_doc": self.root_doc,
                    "exploration_agent_instance": self,
                },
            )
            if finish_loop:
                return self.finish_response

            messages.pop()
            messages.append({"role": "assistant", "content": unparsed_response})
            messages.append({"role": "user", "content": observation})

            num_iters += 1
            if num_iters == self.max_iters:
                raise MaxIterationsReached(num_iters)

        return self.context
