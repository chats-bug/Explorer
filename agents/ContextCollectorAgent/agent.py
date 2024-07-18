import json
from config import config

from utils.doc import Doc
from lib import logger
from tools import ListFiles
from llms import OpenAiLLM, OpenAiChatModels, OpenAIDecodingArguments


class ContextCollectorAgent:
    def __init__(self, root_doc: Doc, max_retries: int = 5):
        self.model = OpenAiChatModels.GPT_4O
        self.llm = OpenAiLLM(model=self.model, config=config)
        self.root_doc = root_doc
        self.max_retries = max_retries
        self.max_iters = 50

        self.user_prompt_format = open(
            "agents/prompts/context_collector_prompt.txt"
        ).read()
        self.list_files_tool = ListFiles(root_doc=root_doc, directory="")

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

        messages = [
            {"role": "system", "content": ""},
            {"role": "user", "content": user_prompt},
        ]

        logger.debug(f"User Prompt: {user_prompt}")

        try:
            response = self.llm.chat(
                messages,
                decoding_args=OpenAIDecodingArguments(
                    temperature=0.5, response_format={"type": "json_object"}
                ),
            )

            response = json.loads(response["content"])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode response: {e}")
            return {"success": False, "response": None}

        return {"success": True, "response": response}
