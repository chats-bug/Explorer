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
                    "response": {
                        "dependency_modules": repo_modules,
                    },
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
