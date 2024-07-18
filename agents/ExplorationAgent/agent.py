import json
from config import config

from utils.doc import Doc
from lib import logger
from tools import ListFiles, ReadCode, ReadCodeSnippet, LSPUtils, Finish
from tools.utils import generate_tools_subprompt
from llms import OpenAiModel, OpenAiChatModels, OpenAIDecodingArguments

from agents import MaxIterationsReached


class ExplorationAgent:
    def __init__(self, root_doc: Doc, max_retries: int = 5):
        self.model = OpenAiChatModels.GPT_4O
        self.llm = OpenAiModel(model=self.model, config=config)
        self.root_doc = root_doc
        self.max_retries = max_retries
        self.max_iters = 50

        self.system_prompt = open("agents/prompts/exploration_prompt.txt").read()
        self.list_files_tool = ListFiles(root_doc=root_doc, directory="")
        self.tools_dictionary = {
            "list_files": ListFiles,
            "read_file": ReadCode,
            "read_code_snippet": ReadCodeSnippet,
            # "lsp": LSPUtils,
            "finish": Finish,
        }
        self.code_flow_graph = None
        self.finish_response = None

    def run(self, directory: str, user_prompt: str):
        self.list_files_tool.directory = directory
        files_list = self.list_files_tool.run()
        if files_list["success"]:
            files_list = files_list["response"]
        else:
            raise Exception("Failed to list files")
        system_prompt = self.system_prompt.format(
            INITIAL_REPO_MAP=files_list,
            AVAILABLE_TOOLS=generate_tools_subprompt(self.tools_dictionary),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.debug(f"System Prompt: {system_prompt}")
        logger.debug(f"User Prompt: {user_prompt}")

        num_iters = 0
        num_tries = 0
        while num_iters < self.max_iters and num_tries < self.max_retries:
            try:
                unparsed_response = self.llm.chat(
                    messages,
                    decoding_args=OpenAIDecodingArguments(
                        temperature=0.5, response_format={"type": "json_object"}
                    ),
                )
                response = json.loads(unparsed_response["content"])
                messages.append(
                    {"role": "assistant", "content": unparsed_response["content"]}
                )
                num_tries = 0
            except Exception as e:
                logger.error(f"Error in chat completion: {e}")
                if num_tries < self.max_retries:
                    num_tries += 1
                    if num_tries == self.max_retries:
                        logger.critical(e)
                    continue
                raise e

            self.code_flow_graph = response.get("exploration", None)
            logger.debug(
                f"[bold bright_white on #5f00ff]   🐳 Code Flow Graph   [/]  \n{self.code_flow_graph}\n"
            )
            logger.debug(
                f"[bold bright_white on #C738BD]   🧠 Thought   [/]  \n{response['thought']}\n"
            )

            tool_name = response["tool"]
            logger.debug(f"[bold bright_white on blue]   🛠️ Tool   [/] \n{tool_name}")
            for key, value in response["tool_args"].items():
                logger.debug(f"  - {key}: {value}")
            if tool_name == "finish":
                self.finish_response = response["tool_args"]
                break
            tool = self.tools_dictionary.get(tool_name, None)
            if tool is None:
                observation = (
                    f"## Observation\nStatus: False\nResponse: Tool not found."
                )
            else:
                tool_instance = tool(
                    **response["tool_args"],
                    root_doc=self.root_doc,
                )
                res = tool_instance.run()
                observation = f"## Observation\nStatus: {res['success']}\nResponse: {res['response']}"

            messages.append({"role": "user", "content": observation})
            logger.debug(
                f"\n[bold bright_white on dark_green]   🔍 Observation   [/] \n{observation}\n"
            )

        if num_tries == self.max_retries:
            raise MaxIterationsReached(num_iters)

        return self.code_flow_graph
