from pydantic import Field
from .base_tool import BaseTool


class Finish(BaseTool):
    """Finishes the process and returns the response to the user."""
    success: str = Field(...,
                         description="Whether the process was successful. Should be 'True' only and only if the "
                                     "original goal is achieved, else 'False'.")
    response: str = Field(..., description="The response to the user.")

    def run(self, *args):
        return {
            "success": self.success,
            "response": self.response
        }
