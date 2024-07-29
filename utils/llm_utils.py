from typing import Union

from llms import OpenAiChatModels, AnthropicModels


def get_request_tokens(
    response,
    model: Union[OpenAiChatModels, AnthropicModels],
):
    if isinstance(model, OpenAiChatModels):
        return response.usage.prompt_tokens, response.usage.completion_tokens
    elif isinstance(model, AnthropicModels):
        return response.usage.input_tokens, response.usage.output_tokens
    else:
        raise ValueError("Invalid model provider")
