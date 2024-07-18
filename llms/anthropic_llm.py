from typing import List, Dict, Union
import anthropic

from config import Config
from lib import logger
from llms.base_llm import BaseLLM
from llms.base_types import AnthropicDecodingArguments, AnthropicModels


class AnthropicLLM(BaseLLM):
    def __init__(self, model: Union[str, AnthropicModels], config: Config):
        super().__init__(model, config)
        self.model_name = model.value if isinstance(model, AnthropicModels) else model
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        decoding_args: AnthropicDecodingArguments = None,
        **kwargs,
    ) -> dict:
        decoding_args = decoding_args or AnthropicDecodingArguments()
        try:
            if messages[0]["role"] == "system":
                decoding_args.system = messages[0]["content"]
                # Remove the system message from the messages list
                messages = messages[1:]
            response = self.client.messages.create(
                model=self.model_name,
                messages=messages,
                **decoding_args.__dict__,
                **kwargs,
            )
            return {"response": response, "content": response.content[0].text}
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return {"response": None, "content": str(e)}
