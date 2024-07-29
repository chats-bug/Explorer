import json
from json import JSONDecodeError

from agents.base_agent import BaseAgent
from config import Config
from typing import List, Optional, Union, Dict, Literal, Type, Tuple

from lib import logger
from llms import (
    OpenAiChatModels,
    OpenAiLLM,
    OpenAIDecodingArguments,
    AnthropicModels,
    AnthropicLLM,
    AnthropicDecodingArguments,
)
from llms.base_llm import BaseLLM
from tools import ReadCode
from utils.llm_utils import get_request_tokens


class PlanAssimilator:
    def __init__(
        self,
        model: Union[OpenAiChatModels, AnthropicModels],
        config: Config,
        title: str,
        max_retries: int = 5,
    ):
        if isinstance(model, OpenAiChatModels):
            self.model = model
            self.llm: BaseLLM = OpenAiLLM(model=self.model, config=config, title=title)
            self.decoding_args = OpenAIDecodingArguments(
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=4096,
            )
        elif isinstance(model, AnthropicModels):
            self.model = model
            self.llm: BaseLLM = AnthropicLLM(
                model=self.model, config=config, title=title
            )
            self.decoding_args = AnthropicDecodingArguments(
                temperature=0.2, max_tokens=4096
            )
        else:
            raise ValueError("Invalid model type")
        self.system_prompt = open(
            "prompts/coding_plan_assimilator_prompt.txt", "r"
        ).read()

        self.input_tokens = 0
        self.output_tokens = 0
        self.plan = None
        self.max_retries = max_retries

        self.read_code_tool = ReadCode(file_path="")

    def run(self, user_query: str, plans: List[Dict]):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"The problem is: {user_query}"},
            {
                "role": "user",
                "content": f"Plan and code details generated for each file \n{json.dumps(plans)}",
            },
        ]

        attempts = 0
        while True:
            try:
                attempts += 1
                response = self.llm.chat(
                    messages=messages,
                    decoding_args=self.decoding_args,
                )
                parsed_response = json.loads(response["content"])
                self.input_tokens, self.output_tokens = get_request_tokens(
                    response=response, model=self.model
                )
                return parsed_response
            except Exception as e:
                logger.error(
                    f"Error in CodePlanning.run: {e}. Retries left = {self.max_retries-attempts}"
                )
                if attempts > self.max_retries:
                    logger.critical(
                        f"Max retries reached in CodePlanning.run: {e}. Aborting."
                    )
                    raise e
