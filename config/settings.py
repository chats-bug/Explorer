import os
from dotenv import load_dotenv
import logging
from rich.console import Console


from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Configuration class for managing settings.

    Attributes:
        - log_level (int): Logging level. Here is a list of logging levels:
                CRITICAL = 50
                FATAL = 50
                ERROR = 40
                WARNING = 30
                WARN = WARNING
                INFO = 20
                DEBUG = 10
                NOTSET = 0
        - openai_api_key (str): API key for OpenAI.
    """

    console: Console = field(init=False)
    log_level_str: str = field(default="INFO")
    log_level: int = field(init=False)
    openai_api_key: str = field(init=False)

    def __post_init__(self):
        self.console = Console()

        load_dotenv()

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.log_level_str = os.getenv("APP_LOG_LEVEL", self.log_level_str)
        self.log_level = getattr(logging, self.log_level_str.upper())
