import json
from typing import Literal

from agents.base_agent import BaseAgent
from config import config

from utils.doc import Doc
from lib import logger
from tools import ListFiles
from llms import OpenAiLLM, OpenAiChatModels, OpenAIDecodingArguments, AnthropicModels


class ContextCollectorAgent(BaseAgent):
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
        self.max_retries = max_retries
        self.max_iters = 50

        self.user_prompt_format = open(
            "agents/prompts/context_collector_prompt.txt"
        ).read()
        self.list_files_tool = ListFiles(root_doc=root_doc, directory="", depth=-1)

    def run(self, directory: str, user_input: str):
        self.list_files_tool.directory = directory
        files_list = self.list_files_tool.run()
        if files_list["success"]:
            files_list = files_list["response"]
        else:
            raise Exception("Failed to list files")
        user_prompt = self.user_prompt_format.format(
            FILE_LIST=files_list, FEATURE_DESCRIPTION=user_input
        )
        system_prompt = (
            "You are an experienced software engineer with years of SWE experience. You should follow whatever"
            "the user requests."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        # messages = [
        #     {"role": "system", "content": system_prompt + "\n" + user_prompt},
        #     {
        #         "role": "user",
        #         "content": f"Please list down all the relevant directories and files for the following feature request: {user_input}",
        #     },
        # ]

        logger.debug(f"System Prompt: {system_prompt}")
        logger.debug(f"User Prompt: {user_prompt}")

        try:
            _, parsed_response = self.get_llm_response(
                messages=messages, parse_response=True
            )
            return {"success": True, "response": parsed_response}
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return {"success": False, "response": str(e)}
