import json
import os.path
from typing import Literal

from agents.base_agent import BaseAgent
from config import config

from utils.doc import Doc
from lib import logger
from tools import ListFiles, DependencyManager
from llms import OpenAiLLM, OpenAiChatModels, OpenAIDecodingArguments, AnthropicModels


class ContextCollectorAgent(BaseAgent):
    def __init__(
        self,
        root_doc: Doc,
        title: str,
        max_retries: int = 5,
        max_iters: int = 50,
        model_provider: Literal["openai", "anthropic"] = "openai",
        max_dependency_analysis_depth: int = 3,
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
        self.tools_dictionary.update({"dependency_manager": DependencyManager})
        self.max_dependency_analysis_depth = max_dependency_analysis_depth

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
        #         "content": f"Please list down all the relevant directories and files"
        #         "for the following feature request: {user_input}",
        #     },
        # ]

        logger.debug(f"System Prompt: {system_prompt}")
        logger.debug(f"User Prompt: {user_prompt}")

        relevant_files = []
        new_files = []
        root_path_abs = os.path.abspath(directory)
        for i in range(self.max_dependency_analysis_depth):
            try:
                response, parsed_response = self.get_llm_response(
                    messages=messages, parse_response=True
                )
                logger.debug(f"[bold red1 on grey3]  Response  [/]:\n{response}")
                if not parsed_response.get("relevant_directories", None):
                    break

                relevant_files.append(parsed_response.get("relevant_directories", {}))
                new_files.append(parsed_response.get("create", {}))

                dependency_prompt = (
                    "Here are the dependencies of the files that you have listed. Go through them and "
                    "list out any files that you think are relevant to the feature request."
                    "If you think that there are no more relevant files, you can respond with an empty dictionary {}.\n"
                    "Remember to follow the same JSON format to respond.\n"
                )
                for _, rel_files in relevant_files[-1].items():
                    for file in rel_files:
                        file_path = file.split(":")[0]
                        tool_response, _ = self.run_tool(
                            "dependency_manager",
                            {
                                "file_path": file_path,
                                "root_path": root_path_abs,
                                "only_repo_modules": True,
                            },
                        )
                        tool_response = tool_response.split("\nResponse: ")[-1]
                        dependency_prompt += f"[File] {os.path.relpath(file_path, root_path_abs)}: {tool_response}\n"
                messages.extend(
                    [
                        {"role": "assistant", "content": response},
                        {"role": "user", "content": dependency_prompt},
                    ]
                )
                logger.debug(f"## USER PROMPT : {dependency_prompt}")
            except Exception as e:
                logger.critical(f"Error in chat completion: {e}")
                return {"success": False, "response": str(e)}

        # relevant_files is a list of dictionaries
        # these dictionaries might have the same keys
        # their values are lists of file paths
        # merge these dictionaries into one
        merged_relevant_files = {}
        for rel_files in relevant_files:
            for key, value in rel_files.items():
                if key not in merged_relevant_files:
                    merged_relevant_files[key] = []
                merged_relevant_files[key].extend(value)
        return {
            "success": True,
            "response": {
                "relevant_files": merged_relevant_files,
                "new_files": new_files,
            },
        }
