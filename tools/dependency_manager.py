from typing import Dict

from pydantic import Field

from utils.dependency_graph import get_imports
from lib import logger
from tools import BaseTool


class DependencyManager(BaseTool):
    """
    This tool retrieves the imports of a specific file from a document directory.
    """

    file_path: str = Field(..., description="The file path to get information about.")
    root_path: str = Field("", description="The path of the root of the repository")
    only_repo_modules: bool = Field(
        True, description="Whether to only include modules from the repository"
    )

    def run(self, *args):
        try:
            repo_modules, python_modules = get_imports(
                path=self.file_path, root_path=self.root_path
            )
            if self.only_repo_modules:
                return {
                    "success": True,
                    # "response": repo_modules,
                    "response": self._format_deps_as_string(repo_modules),
                }
            return {
                "success": True,
                "response": {
                    "dependency_modules": repo_modules,
                    "dependency_packages": python_modules,
                },
            }
        except Exception as e:
            return {"success": False, "response": e.__str__()}

    @staticmethod
    def _format_deps_as_string(dependencies: Dict) -> str:
        formatted_dependency_info = ""
        """
        "superagi.lib.logger": {                                                                                                                                                        
            "imports": [                                                                                                                                                                
                ["logger", null]                                                                                                                                                                       
            ],                                                                                                                                                        
            "line_no": 6                                                                                                                                                                
        }
        """
        for import_statement, import_info in dependencies.items():
            formatted_dependency_info += f"[File] {import_statement}:\n"
            line_no = import_info["line_no"]
            for import_name in import_info["imports"]:
                formatted_dependency_info += f"- [Import] {import_name[0]}"
                if import_name[1]:
                    formatted_dependency_info += f" as {import_name[1]}"
                formatted_dependency_info += "\n"
            formatted_dependency_info += "\n" + "-" * 50 + "\n"
        return formatted_dependency_info
