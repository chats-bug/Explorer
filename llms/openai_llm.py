from typing import List, Optional, Union
from config.settings import Config
from openai import OpenAI
from .base_types import OpenAiChatModels, OpenAIDecodingArguments, ModelType


class OpenAiModel:
    def __init__(
        self,
        model: Union[OpenAiChatModels, str],
        config: Config,
    ):
        self.api_key = config.openai_api_key
        self.model = model
        self.model_name = model.value if isinstance(model, OpenAiChatModels) else model
        self.client = OpenAI(api_key=self.api_key)

    def get_model(self):
        return self.model.value

    def get_token_limit(self):
        return self.model.token_limit

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
                    model_name=self.model.value,
                    messages=messages,
                    decoding_args=decoding_args,
                )
            elif self.model.type == ModelType.IMAGE:
                return self._vision_completion(
                    client=client,
                    model_name=self.model.value,
                    messages=messages,
                    decoding_args=decoding_args,
                )
            elif self.model.type == ModelType.IMAGE_GENERATION:
                return self._image_generation(
                    client=client,
                    model_name=self.model.value,
                    prompt=messages[0],
                    **kwargs,
                )
            else:
                raise ValueError("Model type not supported")

        except Exception as exception:
            raise exception

    @staticmethod
    def _text_completion(
        client,
        model_name: str,
        messages: List,
        decoding_args: OpenAIDecodingArguments,
    ):
        try:
            response = client.chat.completions.create(
                model=model_name, messages=messages, **(decoding_args.__dict__)
            )
            content = response.choices[0].message.content
            return {"response": response, "content": content}

        except Exception as exception:
            raise exception

    @staticmethod
    def _vision_completion(
        client,
        model_name: str,
        messages: List,
        decoding_args: OpenAIDecodingArguments,
    ):
        try:
            response = client.chat.completions.create(
                model=model_name, messages=messages, **(decoding_args.__dict__)
            )
            content = response.choices[0].message.content
            return {"response": response, "content": content}

        except Exception as exception:
            raise exception

    @staticmethod
    def _image_generation(
        client,
        model_name: str,
        prompt: str,
        **kwargs,
    ):
        try:
            # get the response_format from kwargs
            response_format = kwargs["response_format"]
            response = client.images.generate(model=model_name, prompt=prompt, **kwargs)
            if response_format == "url":
                content = response.data[0].url
            elif response_format == "b64":
                content = response.data[0].b64_json
            return {"response": response, "content": content}

        except Exception as exception:
            raise exception
