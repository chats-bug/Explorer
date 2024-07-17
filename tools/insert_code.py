from pydantic import Field

from tools import BaseTool
from utils.linting import default_linter, LinterError


class InsertCode(BaseTool):
    """
    This tool reads a file, inserts code after a specified line number, writes the
    updated content back to the file, and then performs linting on the modified file.
    """

    file_path: str = Field(..., description="The path to the code file.")
    after_line_number: int = Field(
        ..., description="The line number after which to insert the code."
    )
    code: str = Field(..., description="The code to insert.")

    def run(self, *args):
        try:
            with open(self.file_path, "r") as file:
                lines = file.readlines()
        except FileNotFoundError as fnf:
            return {"success": False, "response": fnf.__str__()}

        # adjust start and end line for 0 based indexing
        after_line_number = self.after_line_number - 1

        if after_line_number > len(lines):
            return {
                "success": False,
                "response": f"Line number {self.after_line_number} is out of bounds. File has {len(lines)} lines.",
            }

        new_lines = self.code.split("\n")
        new_lines = [f"{line}\n" for line in new_lines]

        edited_lines = (
            lines[: after_line_number + 1] + new_lines + lines[after_line_number + 1 :]
        )

        with open(self.file_path, "w") as file:
            file.writelines(edited_lines)

        try:
            lint_result = default_linter.lint_file(self.file_path)
        except LinterError as lin_ex:
            return {
                "success": False,
                "response": f"Code has been edited but linting failed. Please check the code for the following issues: {lin_ex}.",
            }

        return {
            "success": True,
            "response": f"Code in {self.file_path} edited successfully. No linting issues found.",
        }
