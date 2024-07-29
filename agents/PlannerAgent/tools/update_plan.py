from typing import Any, Dict, List
from pydantic import BaseModel, Field

from tools import BaseTool


class Task(BaseModel):
    step: int = Field(..., description="The step number of the task.")
    task_description: str = Field(..., description="The description of the task.")
    create: List[str] = Field([], description="The files to create.")
    create_info: str = Field("", description="The information to create in the file.")
    update: List[str] = Field([], description="The files to update.")
    update_info: str = Field(
        "",
        description="The information to update in the file. Mention function names, class names and also line numbers.",
    )
    reference: List[str] = Field(
        [],
        description="The files to reference. Mention all the files that need to be referenced to understand the context.",
    )
    reference_info: str = Field(
        "",
        description="The information to reference in the file. Mention function names, class names and also line "
        "numbers.",
    )

    class Config:
        from_attributes = True


class UpdatePlan(BaseTool):
    """
    This function replaces the current plan with the updated plan. Make sure to pass all the steps in the plan. Use this tool whenever you want to update the plan.
    Every part of the plan must contain either a create or update file. There cannot exist a task without any create or update file.
    REMEMBER: Never update any file without reading the file first. Always make sure to read the file before updating it.
    REMEMBER: Always provide references whenever creating or updating. References are necessary for the user to understand the context of the file.
    """

    planner_agent_instance: Any = Field(
        ..., description="The instance of the PlannerAgent.", exclude=True
    )
    updated_plan: List[Task] = Field(
        ...,
        description="The updated plan to replace the current plan with.",
    )

    def run(self, *args):
        try:
            plan = [
                {
                    "step": t.step,
                    "task": t.task_description,
                    "create": t.create,
                    "update": t.update,
                    "update_info": t.update_info,
                    "reference": t.reference,
                    "reference_info": t.reference_info,
                }
                for t in self.updated_plan
            ]
            self.planner_agent_instance.plan = plan
            return {"success": True, "response": f"Plan updated successfully."}
        except Exception as e:
            return {"success": False, "response": e.__str__()}
