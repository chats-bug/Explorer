from pydantic import Field

from utils.doc import Doc, find_doc
from lib import logger
from tools import BaseTool
from utils.ide_interactions import generate_outline


class FileInfo(BaseTool):
    """
    This tool retrieves information about a specific file from a document directory. It includes the summary and
    documentation of the file by default. Only include documentation / outline if necessary. They are big and take up\
    a lot of context, so avoid using them if possible.
    """

    root_doc: Doc = Field(
        ..., description="The root document to list files in.", exclude=True
    )
    file_path: str = Field(..., description="The file path to get information about.")
    include_summary: bool = Field(
        True, description="Whether to include the summary of the file."
    )
    include_documentation: bool = Field(
        False, description="Whether to include the documentation of the file."
    )
    include_outline: bool = Field(
        False, description="Whether to include the outline of the file."
    )

    def run(self, *args):
        try:
            exclude = ["children"]
            logger.debug(f"Excluding: {exclude}")
            if target_doc := find_doc(self.root_doc, self.file_path):
                return_obj = {
                    k: v for k, v in target_doc.dict().items() if k not in exclude
                }
                if self.include_outline:
                    if outline := generate_outline(target_doc):
                        return_obj["outline"] = outline
                return {"success": True, "response": return_obj}
            return {
                "success": False,
                "response": f"Directory {self.directory} not found in the document.",
            }
        except Exception as e:
            return {"success": False, "response": e.__str__()}
