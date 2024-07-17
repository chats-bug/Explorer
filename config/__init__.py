from .settings import Config

config = Config()
console = config.console

__all__ = ["config", "console"]