from abc import abstractmethod
from pydantic import BaseModel


class BaseTool(BaseModel):
    @abstractmethod
    def run(self, *args) -> dict:
        pass
