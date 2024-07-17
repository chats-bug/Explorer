import json
import questionary
from questionary import Separator
import os

from agents.ContextCollectorAgent import ContextCollectorAgent
from agents.ExplorationAgent import ExplorationAgent
from utils.doc import Doc, DocUtils, get_doc
from lib import logger
from config import console


def run_context_collector_agent(root_doc: Doc, user_input: str, directory: str):
    context_collector_agent = ContextCollectorAgent(root_doc=root_doc)
    response = context_collector_agent.run(directory=directory, user_input=user_input)
    return response


def run_exploration_agent(root_doc: Doc, user_prompt: str, directory: str):
    exploration_agent = ExplorationAgent(root_doc=root_doc)
    response = exploration_agent.run(user_prompt=user_prompt, directory=directory)
    return response


def main():
    questionary.print("Welcome to the New Context Agent!")
    # root_path = questionary.path("Enter the root path of the project:").ask()
    # root_path = os.path.abspath(root_path)
    root_path = "workspace/SuperAGI"
    with console.status("[bold green] Generating documentation..."):
        root_doc = get_doc(root_path)

    user_input = questionary.text("Enter the feature description:").ask()

    directory = questionary.path(
        "Enter the directory path: (Press enter to search in root)"
    ).ask()
    if not directory:
        directory = root_path

    agent_to_run = questionary.select(
        "Select the agent to run:",
        choices=[
            Separator("---- Agents ----"),
            "Exploration Agent",
            "Context Collector Agent",
        ],
        pointer="👉",
        use_indicator=True,
        style=questionary.Style([("highlighted", "fg:#FF9D00 bold reverse")]),
    ).ask()

    if agent_to_run == "Exploration Agent":
        response = run_exploration_agent(root_doc=root_doc, user_prompt=user_input, directory=directory)
        console.print(response)
        return
    else:
        context_collector_agent = ContextCollectorAgent(root_doc=root_doc)
        response = context_collector_agent.run(directory=directory, user_input=user_input)
        console.print(response["response"])


if __name__ == "__main__":
    main()
