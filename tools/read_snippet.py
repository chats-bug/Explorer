import ast
from pydantic import Field
from typing import Literal

from lib import logger
from tools import BaseTool
from utils.ide_interactions import extract_info
from tools.read_code import ReadCode


class ReadCodeSnippet(BaseTool):
    """
    Use this tool to read a code snippet from a file. You need to provide the file path, node name and node type to get.
    For example, if you want to read a function named 'test' from a file 'test.py', you can use this tool.
    """

    file_path: str = Field(..., description="The file path to get information about.")
    node_name: str = Field(..., description="The node name to get information about.")
    node_type: Literal["class", "function", "variable"] = Field(
        ..., description="The node type to get information about."
    )

    def run(self, *args):
        try:
            with open(self.file_path, "r") as file:
                code = file.read()

            # Parse the source code into AST.
            tree = ast.parse(code)

            # Initialize the store for extracted information.
            accumulated = {"class": [], "function": [], "variable": []}
            extract_info(tree, accumulated)

            for node in accumulated[self.node_type]:
                if node["name"] == self.node_name:
                    file_info_tool = ReadCode(
                        file_path=self.file_path,
                        start_line=node["line_nos"][0],
                        end_line=node["line_nos"][1],
                    )
                    read_code_tool_response = file_info_tool.run()
                    if not read_code_tool_response["success"]:
                        return {
                            "success": False,
                            "response": f"Error in reading code snippet: {read_code_tool_response['response']}",
                        }
                    return {
                        "success": True,
                        "response": {
                            "start_line": node["line_nos"][0],
                            "end_line": node["line_nos"][1],
                            "code": read_code_tool_response["response"],
                        }
                    }

            # if node is not found
            return {
                "success": False,
                "response": f"Node with name '{self.node_name}' and type '{self.node_type}' not found in file '{self.file_path}'.",
            }
        except FileNotFoundError as fnf:
            return {"success": False, "response": fnf.__str__()}
        except Exception as e:
            logger.critical(f"Error in reading code snippet: {e}")
            return {"success": False, "response": e.__str__()}
