from typing import List, Optional, Union
from config.settings import Config
from openai import OpenAI

from .base_llm import BaseLLM
from .base_types import OpenAiChatModels, OpenAIDecodingArguments, ModelType


class OpenAiLLM(BaseLLM):
    def __init__(self, model: OpenAiChatModels, config: Config, title: str):
        super().__init__(model=model, config=config, title=title)
        self.api_key = config.openai_api_key
        self.client = OpenAI(api_key=self.api_key)

    def get_model(self):
        return self.model.value

    def chat(
        self,
        messages: List,
        decoding_args: Optional[OpenAIDecodingArguments] = None,
        **kwargs,
    ) -> dict:
        assert len(messages) > 0, "Messages list cannot be empty"
        try:
            client = self.client
            if self.model.type == ModelType.TEXT:
                return self._text_completion(
                    client=client,
                    messages=messages,
                    decoding_args=decoding_args,
                    **kwargs,
                )
            elif self.model.type == ModelType.IMAGE:
                return self._vision_completion(
                    client=client,
                    model_name=self.model_name,
                    messages=messages,
                    decoding_args=decoding_args,
                    **kwargs,
                )
            elif self.model.type == ModelType.IMAGE_GENERATION:
                return self._image_generation(
                    client=client,
                    model_name=self.model_name,
                    prompt=messages[0],
                    **kwargs,
                )
            else:
                raise ValueError("Model type not supported")

        except Exception as exception:
            raise exception

    def _text_completion(
        self,
        client,
        messages: List,
        decoding_args: OpenAIDecodingArguments,
        **kwargs,
    ):
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **decoding_args.__dict__,
                **kwargs,
            )
            content = response.choices[0].message.content
            self.log_tokens(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                title=self.title,
            )
            return {"response": response, "content": content}

        except Exception as exception:
            raise exception

    def _vision_completion(
        self,
        messages: List,
        decoding_args: OpenAIDecodingArguments,
        **kwargs,
    ):
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **decoding_args.__dict__,
                **kwargs,
            )
            self.log_tokens(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                title=self.title,
            )
            content = response.choices[0].message.content
            return {"response": response, "content": content}

        except Exception as exception:
            raise exception

    def _image_generation(
        self,
        prompt: str,
        **kwargs,
    ):
        try:
            # get the response_format from kwargs
            response_format = kwargs["response_format"]
            response = self.client.images.generate(
                model=self.model_name, prompt=prompt, **kwargs
            )
            self.log_tokens(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                title=self.title,
            )
            content = ""
            if response_format == "url":
                content = response.data[0].url
            elif response_format == "b64":
                content = response.data[0].b64_json
            return {"response": response, "content": content}

        except Exception as exception:
            raise exception
