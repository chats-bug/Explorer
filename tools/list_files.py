import json
from typing import Dict, List

from pydantic import Field
import os

from utils.doc import Doc, find_doc
from lib import logger
from tools import BaseTool


# This class likely represents a tool for listing files.
class ListFiles(BaseTool):
    """
    The function retrieves target files from a document directory, returning a success status and response.
    It can also filter files based on the file extension and include the summary and documentation of the file if asked.
    """

    root_doc: Doc = Field(
        ..., description="The root document to list files in.", exclude=True
    )
    directory: str = Field(..., description="The directory to list files in.")

    # TODO: The file extension flag is temporarily disabled to check for planning improvements

    file_extension: str = Field(
        "", description="The file extension to filter files by.", exclude=True
    )
    include_summary: bool = Field(
        False, description="Whether to include the summary of the file.", exclude=True
    )
    include_documentation: bool = Field(
        False,
        description="Whether to include the documentation of the file.",
        exclude=True,
    )
    depth: int = Field(
        1, description="The depth to list down files in a directory.", exclude=True
    )

    def run(self, *args):
        try:
            exclude = (
                # ["children"]
                (["documentation"] if not self.include_documentation else [])
                + (["summary"] if not self.include_summary else [])
            )
            if target_doc := find_doc(self.root_doc, self.directory):
                target_files = []
                for child in target_doc.children:
                    # logger.debug(f"File found: {child.path}")
                    if child.path.endswith(self.file_extension):
                        # logger.debug(f"File extension matched: {self.file_extension}")
                        target_files.append(
                            {
                                k: v
                                for k, v in child.model_dump().items()
                                if k not in exclude
                            }
                        )
                        target_files[-1]["type"] = (
                            "file" if os.path.isfile(child.path) else "directory"
                        )
                return {
                    "success": True,
                    "response": "\n".join(self._format_output(target_files)),
                }
            return {
                "success": False,
                "response": f"Directory {self.directory} not found in the document.",
            }
        except Exception as e:
            logger.critical(e)
            return {"success": False, "response": e.__str__()}

    def _format_output(self, files_and_dirs: List[Dict], level: int = 0):
        formatted_output = []
        for file_or_dir in files_and_dirs:
            if os.path.isfile(file_or_dir["path"]):
                formatted_output.append(f"- [File]: {file_or_dir['path']}")
            else:
                formatted_children_output = []
                if file_or_dir["children"] and (level < self.depth or self.depth == -1):
                    formatted_children_output = self._format_output(
                        file_or_dir["children"],
                        level=level + 1,
                    )
                if formatted_children_output:
                    formatted_str = f"v [Dir]: {file_or_dir['path']}"
                    formatted_str += ":"
                    for child_str in formatted_children_output:
                        formatted_str += "\n" + "\t" * (level + 1) + child_str
                else:
                    formatted_str = f"> [Dir]: {file_or_dir['path']}"
                formatted_output.append(formatted_str)

        return formatted_output
