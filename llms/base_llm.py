# Implement a base llm type with the following init parameters:
# model: str
# config: Config

# There should be an abstract method get_model that returns the model value
# There should be an abstract method get_token_limit that returns the model token limit
# There should be an abstract method `chat` that takes messages and returns a dictionary

from abc import ABC, abstractmethod
from config import Config
from typing import List, Optional, Union, Dict


class BaseLLM(ABC):
    def __init__(self, model: str, config: Config):
        self.model = model
        self.config = config

    @abstractmethod
    def chat(self, messages: List, decoding_args: Dict, **kwargs) -> dict:
        pass
