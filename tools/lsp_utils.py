import os
import json
from typing import Dict, List, Optional
from pydantic import Field
from dataclasses import dataclass
from enum import Enum

from monitors4codegen.multilspy import SyncLanguageServer
from monitors4codegen.multilspy.multilspy_config import MultilspyConfig
from monitors4codegen.multilspy.multilspy_logger import MultilspyLogger

from lib import logger
from tools import BaseTool


class SupportedLanguages(Enum):
    PYTHON = "python"
    RUST = "rust"
    CSHARP = "csharp"
    JAVA = "java"


class RequestTypes(Enum):
    DEFINITION = "definition"
    COMPLETIONS = "completions"
    REFERENCES = "references"
    DOCUMENT_SYMBOLS = "document_symbols"
    HOVER = "hover"


class LSPUtils(BaseTool):
    """
    This tool is used to make requests to the Language Server Protocol (LSP) for a given file. Use this to jump to definitions or find references of a symbol in a file.
    """

    language: SupportedLanguages = Field(..., description="The language of the code.")
    repo_path: str = Field(..., description="The path to the repository.")
    file_path: str = Field(..., description="The path to the file.")
    line_number: int = Field(
        ..., description="The line number of the symbol. (1-INDEXED)"
    )
    column_number: Optional[int] = Field(
        None, description="The column number of the symbol.", exclude=True
    )
    symbol: Optional[str] = Field(
        None, description="The symbol for which the request is being made."
    )
    request_type: RequestTypes = Field(..., description="The type of request to make.")

    def run(self, *args):
        try:
            assert (self.column_number is not None) or (
                self.symbol is not None
            ), "Either column_number or symbol must be provided."

            config = MultilspyConfig.from_dict({"code_language": self.language.value})
            lsp_logger = MultilspyLogger()
            lsp = SyncLanguageServer.create(config, lsp_logger, self.repo_path)

            # Make the line number zero indexed
            self.line_number -= 1
            # Find the column number of the symbol if provided
            if self.column_number is None:
                with open(self.file_path) as f:
                    lines = f.readlines()
                    line = lines[self.line_number]
                    self.column_number = line.find(self.symbol)
            if self.symbol is None:
                with open(self.file_path) as f:
                    lines = f.readlines()
                    line = lines[self.line_number]
                    # symbol should start from the column number and end at the first space
                    self.symbol = line[self.column_number :].split(" ")[0]

            with lsp.start_server():
                if self.request_type == RequestTypes.DEFINITION:
                    result = lsp.request_definition(
                        self.file_path, self.line_number, self.column_number
                    )
                elif self.request_type == RequestTypes.COMPLETIONS:
                    result = lsp.request_completions(
                        self.file_path, self.line_number, self.column_number
                    )
                elif self.request_type == RequestTypes.REFERENCES:
                    result = lsp.request_references(
                        self.file_path, self.line_number, self.column_number
                    )
                elif self.request_type == RequestTypes.DOCUMENT_SYMBOLS:
                    result = lsp.request_document_symbols(self.file_path)
                elif self.request_type == RequestTypes.HOVER:
                    result = lsp.request_hover(
                        self.file_path, self.line_number, self.column_number
                    )
                else:
                    return {"success": False, "response": "Invalid request type."}
                # logger.info(
                #     f"Requesting {self.request_type} for {self.symbol} at line {self.line_number+1}, column {self.column_number+1} in {self.file_path} :: {result[0]['relativePath']}"
                # )
                return {"success": True, "response": result}
        except Exception as e:
            logger.critical(f"Failed to make LSP request: {e}")
            return {"success": False, "response": e.__str__()}
