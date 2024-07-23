# Implement a base llm type with the following init parameters:
# model: str
# config: Config
import dataclasses

# There should be an abstract method get_model that returns the model value
# There should be an abstract method get_token_limit that returns the model token limit
# There should be an abstract method `chat` that takes messages and returns a dictionary

from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Tuple, Type

from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table

from config import Config, console
from llms.base_types import (
    OpenAiChatModels,
    AnthropicModels,
    OpenAIDecodingArguments,
    AnthropicDecodingArguments,
)


class BaseLLM(ABC):
    def __init__(
        self,
        model: Union[OpenAiChatModels, AnthropicModels],
        config: Config,
        title: str,
    ):
        self.model = model
        self.model_name = str(model.value)
        self.config = config
        self.title = title

    @abstractmethod
    def chat(
        self,
        messages: List,
        decoding_args: Union[OpenAIDecodingArguments, AnthropicDecodingArguments],
        **kwargs,
    ) -> dict:
        pass

    def get_token_limit(self) -> Tuple[int, int]:
        return self.model.token_limit

    def log_tokens(self, input_tokens: int, output_tokens: int, title: str = ""):
        title = title or self.title
        max_input_tokens, max_output_tokens = self.get_token_limit()

        input_percentage = input_tokens / max_input_tokens
        output_percentage = output_tokens / max_output_tokens

        # Make a unit that looks like this:
        # do a match case on the percentage and return a string
        def return_color(percentage: float) -> str:
            if percentage < 0.25:
                return "green"
            elif percentage < 0.5:
                return "yellow"
            elif percentage < 0.75:
                return "indian_red1"
            else:
                return "deep_pink2"

        input_color = return_color(input_percentage)
        output_color = return_color(output_percentage)

        grid = Table.grid(expand=True, padding=(0, 3))
        grid.add_column(justify="right")
        grid.add_column(justify="right")
        grid.add_column(justify="right")

        grid.add_row(
            "Input",
            ProgressBar(
                total=max_input_tokens,
                completed=input_tokens,
            ),
            f"([{input_color}]{input_tokens}[/]/{max_input_tokens}) • [{input_color}]{input_percentage:.2%}[/]",
        )
        grid.add_row(
            "Output",
            ProgressBar(
                total=max_output_tokens,
                completed=output_tokens,
            ),
            f"([{output_color}]{output_tokens}[/]/{max_output_tokens}) • [{output_color}]{output_percentage:.2%}[/]",
        )
        console.print(Panel(grid, title=title, expand=True))
