from typing import List, Dict, Union, Any
from pydantic import Field

from tools import BaseTool


class UpdateContext(BaseTool):
    """
    This tool is used when you need to update the findings of the code repo. You can update the context with the code
    flow graph, relevant files, and relevant directories.
    """

    exploration_agent_instance: Any = Field(
        ..., description="The instance of the ExplorationAgent.", exclude=True
    )
    explanation: str = Field(..., description="The explanation of the code flow graph.")
    code_flow_graph: str = Field(
        ..., description="The call graph of the code in Mermaid format."
    )
    relevant_files: List[str] = Field(..., description="The list of relevant files.")
    similar_feature_dirs: List[Dict[str, Union[str, List[str]]]] = Field(
        ..., description="The list of relevant directories."
    )

    def run(self, *args):
        current_context_backup = None
        try:
            current_context_backup = self.exploration_agent_instance.context.copy()
            self.exploration_agent_instance.context = {
                "explanation": self.explanation,
                "code_flow_graph": self.code_flow_graph,
                "relevant_files": self.relevant_files,
                "similar_feature_dirs": self.similar_feature_dirs,
            }
            return {"success": True, "response": "Context updated successfully"}
        except Exception as exception:
            # Restore the context if an exception occurs
            self.exploration_agent_instance.context = current_context_backup
            return {"success": False, "response": str(exception)}
