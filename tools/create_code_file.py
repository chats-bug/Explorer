import os

from pydantic import Field

from tools import BaseTool
from utils.linting import default_linter, LinterError


class CreateCodeFile(BaseTool):
    """
    This tool creates a new file and writes code to it. It also performs linting on the code.
    If the file already exists, it can be replaced with the new code.
    """

    file_path: str = Field(..., description="The path to the code file.")
    code: str = Field(..., description="The code to write to the file.")
    replace: bool = Field(
        False, description="Whether to replace the file if it already exists."
    )

    def run(self, *args):
        # check if the file already exists
        if os.path.exists(self.file_path) and not self.replace:
            return {
                "success": False,
                "response": f"File {self.file_path} already exists. Please edit / replace the file if you want to "
                f"replace the contents.",
            }

        with open(self.file_path, "w") as file:
            file.write(self.code)

        try:
            lint_result = default_linter.lint_file(self.file_path)
        except LinterError as lin_ex:
            return {
                "success": False,
                "response": f"Code has been written but linting failed. Please check the code for the following issues: {lin_ex}.",
            }

        return {
            "success": True,
            "response": f"Code written to {self.file_path} successfully. No linting issues found.",
        }
