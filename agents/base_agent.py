import json
from abc import ABC, abstractmethod
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
from tools import BaseTool, Finish


class BaseAgent(ABC):
    def __init__(
        self,
        model: Union[OpenAiChatModels, AnthropicModels],
        config: Config,
        return_type: Literal["json_object", "text"],
        max_retries: int = 5,
        max_iters: int = 50,
    ):
        self.llm_expected_return_type = return_type
        if isinstance(model, OpenAiChatModels):
            self.model = model
            self.llm: BaseLLM = OpenAiLLM(model=self.model, config=config)
            self.decoding_args = OpenAIDecodingArguments(
                temperature=0.5, response_format={"type": return_type}, max_tokens=4096
            )
        elif isinstance(model, AnthropicModels):
            self.model = model
            self.llm: BaseLLM = AnthropicLLM(model=self.model, config=config)
            self.decoding_args = AnthropicDecodingArguments(
                temperature=0.5, max_tokens=4096
            )
        else:
            raise ValueError("Invalid model type")

        self.config = config
        self.max_retries = max_retries
        self.max_iters = max_iters

        self.tools_dictionary: Dict[str, Type[BaseTool]] = {"finish": Finish}
        self.finish_response = None
        self.action_graph = []

    @abstractmethod
    def run(self, *args, **kwargs): ...

    def get_model(self) -> str:
        return str(self.model)

    def get_llm_response(
        self, messages: List[Dict[str, str]], parse_response: bool = True, **kwargs
    ) -> Tuple[str, Optional[Dict]]:
        num_tries = 0
        parsed_response_object: Optional[Dict] = None
        while num_tries < self.max_retries:
            try:
                response = self.llm.chat(
                    messages=messages, decoding_args=self.decoding_args, **kwargs
                )
                if self.llm_expected_return_type == "json_object" and parse_response:
                    parsed_response_object = json.loads(response["content"])
                return response["content"], parsed_response_object
            except json.JSONDecodeError as jde:
                logger.error(f"Error parsing LLM Response: {jde}")
                num_tries += 1
                if num_tries == self.max_retries:
                    raise jde
            except Exception as e:
                logger.error(f"Error generating LLM Response: {e}")
                num_tries += 1
                if num_tries == self.max_retries:
                    raise e

    def run_tool(
        self, tool_name: Optional[str], tool_args: Dict, extra_args: Dict
    ) -> Tuple[str, bool]:
        """
        Run the tool with the given name and arguments.
        Returns the observation and a boolean indicating if the tool is a finish tool.
        """
        self.action_graph.append(
            {
                "action": tool_name,
                "args": tool_args,
            }
        )
        tool_class = self.tools_dictionary.get(tool_name)
        if tool_class is None:
            if tool_name:
                observation = f"## Observation\nStatus: False\nResponse: Tool {tool_name} not found."
            else:
                observation = (
                    f"## Observation\nStatus: False\nResponse: No tool name provided."
                )
        else:
            try:
                tool_instance = tool_class(
                    **tool_args,
                    **extra_args,
                )
                response = tool_instance.run()
                observation = f"## Observation\nStatus: {response['success']}\nResponse: {response['response']}"
            except Exception as e:
                observation = f"## Observation\nStatus: False\nResponse: {str(e)}"
                logger.error(
                    f"Error running tool {tool_name} with args {tool_args}: {e}"
                )

        logger.debug(f"[bold bright_white on blue]   🛠️ Tool   [/] \n{tool_name}")
        for arg, value in tool_args.items():
            logger.debug(f"  - {arg}: {value}")
        logger.debug(
            f"\n[bold bright_white on dark_green]   🔍 Observation   [/] \n{observation}\n"
        )
        if tool_name == "finish":
            self.finish_response = tool_args
        return observation, tool_name == "finish"
