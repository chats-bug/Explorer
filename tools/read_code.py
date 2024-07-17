from pydantic import Field

from tools import BaseTool


class ReadCode(BaseTool):
    """
    This tool reads a file and returns the code between specified line numbers. \
    It can also run the linter on the code if specified (default is False). \
    Only reads 200 lines of code at most at a time.
    """

    file_path: str = Field(..., description="The path to the code file.")
    start_line: int = Field(1, description="The starting line number.")
    end_line: int = Field(100, description="The ending line number.")
    lint: bool = Field(False, description="Whether to run the linter on the code.")

    def run(self, *args, **kwargs):
        if 1 < self.end_line < self.start_line:
            return {
                "success": False,
                "response": "`end_line` should be greater than or equal to start_line",
            }
        feedback = ""
        if self.end_line - self.start_line > 200:
            self.end_line = self.start_line + 200
            feedback = "(Code snippet too long; only 200 lines shown)"

        try:
            with open(self.file_path, "r") as file:
                lines = file.readlines()

                start_line = max(self.start_line, 1) - 1
                end_line = (
                    len(lines)
                    if (self.end_line > len(lines) or self.end_line < 0)
                    else self.end_line
                ) - 1

                # check if the file is too short
                if start_line >= len(lines) or end_line > len(lines):
                    return {
                        "success": False,
                        "response": "The file only contains {} lines".format(
                            len(lines)
                        ),
                    }

                code = (
                    f"[File: {self.file_path} ({len(lines)} lines total)] {feedback}\n"
                )
                if not start_line == 0:
                    code += f"({start_line} line(s) above)\n"
                for i in range(start_line, end_line + 1):
                    code += f"{i + 1}:{lines[i]}"
                if not end_line == len(lines) - 1:
                    code += f"({len(lines) - (end_line + 1)} lines below)\n"

                return {"success": True, "response": code}

        except FileNotFoundError as fnf:
            return {"success": False, "response": fnf.__str__()}

        except Exception as e:
            return {"success": False, "response": e.__str__()}
