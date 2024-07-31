import os
from typing import List, Dict, Optional, Literal

from agents.base_agent import BaseAgent
from config import Config
from llms import OpenAiChatModels, AnthropicModels
from utils.doc import Doc
from lib import logger


class CoreLoopDeveloperAgent(BaseAgent):
    def __init__(
        self,
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
            config=Config(),
            return_type="text",
            max_retries=max_retries,
            max_iters=max_iters,
            title=title,
        )

        self.system_prompt = open("agents/prompts/core_loop_prompt.txt").read()

    def run(self, user_input: str, file_list: Optional[List[str]] = None, prev_changes: str = ""):
        self.action_graph = []
        input_context = self.create_input_context(file_list)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"The current codebase is:\n{input_context}"},
            {"role": "user", "content": user_input},
            {"role": "user", "content": f"Changes made to the code bases: {prev_changes}"},
        ]
        logger.debug(f"SYSTEM PROMPT: \n{self.system_prompt}\n")
        logger.debug(f"CONTEXT: \n{input_context}\n")
        logger.debug(f"USER PROMPT: \n{user_input}\n")

        num_attempts = 0
        response, _ = self.get_llm_response(messages=messages, parse_response=False)
        return response

    @staticmethod
    def create_input_context(file_list: List[str]) -> str:
        if not file_list:
            # change from og core loop
            # dumped all the files in the codebase
            return "No specific files provided. Please provide file paths to analyze the codebase."

        context = ""
        for file_path in file_list:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    context += f"|filename| : {file_path}\n|code| : \n{content}\n\n"
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
        return context
