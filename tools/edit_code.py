from pydantic import Field

from utils.linting import default_linter, LinterError
from tools import BaseTool


class EditCode(BaseTool):
    """
    This tool reads a file, edits the code between specified line numbers, writes the
    updated content back to the file, and then performs linting on the modified file.
    """

    file_path: str = Field(..., description="The path to the code file.")
    start_line: int = Field(..., description="The starting line number.")
    end_line: int = Field(..., description="The ending line number.")
    code: str = Field(..., description="The new code to replace with.")
    lint: bool = Field(
        False, description="Whether to perform linting after editing.", exclude=True
    )

    def run(self, *args):
        with open(self.file_path, "r") as file:
            lines = file.readlines()

        # adjust start and end line for 0 based indexing
        start_line = self.start_line - 1
        end_line = self.end_line - 1

        new_lines = self.code.split("\n")
        new_lines = [f"{line}\n" for line in new_lines]

        edited_lines = lines[:start_line] + new_lines + lines[end_line + 1 :]

        with open(self.file_path, "w") as file:
            file.writelines(edited_lines)

        if self.lint:
            try:
                lint_result = default_linter.lint_file(self.file_path)
            except LinterError as lin_ex:
                return {
                    "success": False,
                    "response": f"Code has been edited but linting failed. Please check the code for the following issues: {lin_ex}. No code changes were applied. Rewrite the section avoiding these problems",
                }

        return {
            "success": True,
            "response": f"Code in {self.file_path} edited successfully. No linting issues found.",
        }
