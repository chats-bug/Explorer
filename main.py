import datetime
import json
from typing import Literal, List

import questionary
from questionary import Separator
import os

from lib import logger
from config import console, config
from utils.doc import Doc, DocUtils, get_doc
from agents.ContextCollectorAgent import ContextCollectorAgent
from agents.ExplorationAgent import ExplorationAgent
from agents.PlannerAgent.agent import PlannerAgent
from tools import ListFiles, ReadCode, ReadCodeSnippet, LSPUtils, Finish
from llms import (
    OpenAiLLM,
    OpenAiChatModels,
    OpenAIDecodingArguments,
    AnthropicLLM,
    AnthropicDecodingArguments,
    AnthropicModels,
)
from uuid import uuid4


def run_context_collector_agent(
    root_doc: Doc, user_input: str, directory: str, title: str, id: str
):
    context_collector_agent = ContextCollectorAgent(
        root_doc=root_doc, title=title, max_dependency_analysis_depth=3
    )
    response = context_collector_agent.run(directory=directory, user_input=user_input)
    dir_path = f"saved_states/features/{id}/context_collector"
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "prompts.txt"), "w") as f:
        f.write(f"# USER REQUEST\n{user_input}")
    with open(os.path.join(dir_path, "output.json"), "w") as f:
        f.write(json.dumps(response, indent=4))
    return response


def run_exploration_agent(root_doc: Doc, user_prompt: str, directory: str, id: str):
    directory_overview = ListFiles(root_doc=root_doc, directory=directory).run()
    exploration_prompt = transform_query_to_exploration_prompt(
        query=user_prompt, directory_overview=directory_overview["response"]
    )
    exploration_prompt += (
        "\n"
        "Always remember to note how the directory structure for this particular feature, "
        "and how and where it is being integrated in the codebase."
    )
    logger.info(f"Exploration Prompt: {exploration_prompt}")
    exploration_agent = ExplorationAgent(root_doc=root_doc, title="Exploration Agent")
    response = exploration_agent.run(
        user_prompt=exploration_prompt, directory=directory
    )
    exploration_context = exploration_agent.context
    dir_path = f"saved_states/features/{id}/exploration"
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "prompts.txt"), "w") as f:
        prompt_str = (
            f"# USER REQUEST\n{user_prompt}\n# EXPLORATION PROMPT\n{exploration_prompt}"
        )
        f.write(prompt_str)
    with open(os.path.join(dir_path, "output.json"), "w") as f:
        f.write(json.dumps(exploration_context, indent=4))
    with open(os.path.join(dir_path, "finish_response.json"), "w") as f:
        f.write(json.dumps(response, indent=4))
    with open(os.path.join(dir_path, "action_graph.json"), "w") as f:
        f.write(json.dumps(exploration_agent.action_graph, indent=4))
    with open(os.path.join(dir_path, "token_counts.json"), "w") as f:
        f.write(
            json.dumps(
                {
                    "prompt_tokens": exploration_agent.prompt_tokens,
                    "completion_tokens": exploration_agent.completion_tokens,
                },
                indent=4,
            )
        )
    return exploration_context


def transform_query_to_exploration_prompt(query: str, directory_overview: str):
    llm = OpenAiLLM(
        model=OpenAiChatModels.GPT_4O, config=config, title="Query to Exploration"
    )
    an_llm = AnthropicLLM(
        model=AnthropicModels.CLAUDE_3_5_SONNET_20240620,
        config=config,
        title="Query to Exploration",
    )
    response = llm.chat(
        messages=[
            {"role": "system", "content": "You are a helpful coding assistant"},
            {
                "role": "user",
                "content": "You will be given a user feature request for a particular code repository. You will "
                "transform this request into a request to explore similar features in the repository.\n"
                "For example, if the user asks for a feature to add a delete button to the 'fill details' "
                "section, you will ask the assistant to explore how delete buttons are implemented in the "
                "other sections of the repository and how other buttons are implemented in the 'fill "
                "details' section\n"
                "Here is the directory overview of the repository:\n"
                f"{directory_overview}\n"
                f"User Feature Request: {query}"
                "Always return your exploration prompt with numbered points to clearly indicate all the things that need to be explore. \n"
                "Reply only in the following JSON format:"
                """{
                "thought": "What should be an appropriate exploration prompt for the user feature request?",
                "exploration_prompt: "<exploration_prompt>"
                }
                RETURN ONLY THE JSON""",
            },
        ],
        decoding_args=OpenAIDecodingArguments(
            temperature=0.1,
            response_format={"type": "json_object"},
        ),
        # decoding_args=AnthropicDecodingArguments(temperature=0.1),
    )
    response = json.loads(response["content"])
    return response["exploration_prompt"]


def run_planner_agent(
    root_doc: Doc,
    user_prompt: str,
    directory: str,
    exploration_context: dict,
    model_provider: Literal["openai", "anthropic"],
    id: str,
):
    formatted_str = ""
    if exploration_context:
        formatted_str = ""
        formatted_str += f"Explanation:\n{exploration_context.get('explanation')}\n"
        formatted_str += (
            f"Code Flow Graph:\n{exploration_context.get('code_flow_graph')}\n"
        )
        formatted_str += f"Relevant Files:\n"
        read_code = ReadCode(
            root_doc=root_doc, file_path="", start_line=0, end_line=500, max_lines=500
        )
        for f in exploration_context.get("relevant_files"):
            file_name = f.split(":")[0]
            read_code.file_path = file_name
            res = read_code.run()
            formatted_str += f"- {f}\n"
            formatted_str += res["response"]
            formatted_str += "\n" + "-" * 50 + "\n"
        formatted_str += (
            f"Relevant Directories:\n{exploration_context.get('similar_feature_dirs')}"
        )
    planer_agent = PlannerAgent(
        root_doc=root_doc, model_provider=model_provider, title="Planner Agent"
    )
    response = planer_agent.run(
        directory=directory,
        user_prompt=user_prompt,
        exploration_context=formatted_str,
    )
    # console.print(f"Final Response: {planer_agent.finish_response}")
    # console.print(f"Final Plan: \n{planer_agent.plan}")
    # console.print(f"Action graph: \n{json.dumps(planer_agent.action_graph, indent=4)}")
    # logger.info(
    #     f"Total tokens: {planer_agent.prompt_tokens}, {planer_agent.completion_tokens}"
    # )
    dir_path = f"saved_states/features/{id}/planner"
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "prompts.txt"), "w") as f:
        prompt_str = (
            f"# USER REQUEST\n{user_prompt}\n# EXPLORATION CONTEXT\n{formatted_str}"
        )
        f.write(prompt_str)

    with open(os.path.join(dir_path, "output.json"), "w") as f:
        f.write(json.dumps(planer_agent.plan, indent=4))

    with open(os.path.join(dir_path, "finish_response.json"), "w") as f:
        f.write(json.dumps(planer_agent.finish_response, indent=4))

    with open(os.path.join(dir_path, "action_graph.json"), "w") as f:
        f.write(json.dumps(planer_agent.action_graph, indent=4))

    with open(os.path.join(dir_path, "token_counts.json"), "w") as f:
        f.write(
            json.dumps(
                {
                    "prompt_tokens": planer_agent.prompt_tokens,
                    "completion_tokens": planer_agent.completion_tokens,
                },
                indent=4,
            )
        )

    return response


def main():
    questionary.print("Welcome to the New Context Agent!")
    root_path = questionary.path("Enter the root path of the project:").ask()
    # root_path = os.path.abspath(root_path)
    with console.status("[bold green] Fetching documentation..."):
        root_doc = get_doc(root_path)

    directory = questionary.path(
        "Enter the directory path: (Press enter to search in root)"
    ).ask()
    if not directory:
        directory = root_path

    user_input = questionary.text("Enter the feature description:").ask()

    agent_to_run = questionary.select(
        "Select the agent to run:",
        choices=[
            Separator("---- Agents ----"),
            "Exploration Agent",
            "Context Collector Agent",
            "Planner Agent",
        ],
        pointer="👉",
        use_indicator=True,
        style=questionary.Style([("highlighted", "fg:#FF9D00 bold reverse")]),
    ).ask()
    model_choice = questionary.select(
        "Select the model to use:",
        choices=[
            Separator("---- Models ----"),
            "OpenAI: GPT-4O",
            "Anthropic: Claude 3.5 Sonnet",
        ],
        pointer="👉",
        use_indicator=True,
        style=questionary.Style([("highlighted", "fg:#FF9D00 bold reverse")]),
    ).ask()

    if agent_to_run == "Exploration Agent":
        directory_overview = ListFiles(root_doc=root_doc, directory=directory).run()
        exploration_prompt = transform_query_to_exploration_prompt(
            query=user_input, directory_overview=directory_overview["response"]
        )
        exploration_prompt += (
            "\n"
            "Always remember to note how the directory structure for this particular feature, "
            "and how and where it is being integrated in the codebase.\n"
            # "The entry point of the repo is main.py, always start from there."
        )
        logger.info(f"Exploration Prompt: {exploration_prompt}")
        exploration_agent = ExplorationAgent(
            root_doc=root_doc,
            model_provider="openai" if "OpenAI" in model_choice else "anthropic",
            title="Exploration Agent",
        )
        response = exploration_agent.run(
            user_prompt=exploration_prompt,
            directory=directory,
        )
        exploration_context = exploration_agent.context
        logger.info(
            f"Total tokens: {exploration_agent.prompt_tokens}, {exploration_agent.completion_tokens}"
        )
        file_path = f"saved_states/exploration/state_2.json"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(json.dumps(exploration_context, indent=4))
    elif agent_to_run == "Context Collector Agent":
        response = run_context_collector_agent(
            root_doc=root_doc,
            user_input=user_input,
            directory=directory,
            title="Context Collector",
        )
        console.print(response["response"])
    else:
        exp_file_path = "saved_states/exploration/state_2.json"
        logger.info(f"Reading exploration context {exp_file_path}")
        exploration_context = open(exp_file_path).read()
        exploration_context = json.loads(exploration_context)
        _ = run_planner_agent(
            root_doc=root_doc,
            user_prompt=user_input,
            directory=directory,
            exploration_context=exploration_context,
            model_provider="openai" if "OpenAI" in model_choice else "anthropic",
        )


def run_explorer_planner_context_collector(
    root_path: str,
    directory: str,
    user_request: str,
    model_provider: Literal["openai", "anthropic"] = "openai",
):
    task_id = str(uuid4())
    logger.info(f"RUNNING TASK ID: {task_id}; USER REQUEST: {user_request}")

    # with console.status("[bold green] Fetching documentation..."):
    root_doc = get_doc(root_path)

    exploration_context = run_exploration_agent(
        root_doc=root_doc,
        user_prompt=user_request,
        directory=directory,
        id=task_id,
    )

    _ = run_planner_agent(
        root_doc=root_doc,
        user_prompt=user_request,
        directory=directory,
        exploration_context=exploration_context,
        model_provider=model_provider,
        id=task_id,
    )

    run_context_collector_agent(
        root_doc=root_doc,
        user_input=user_request,
        directory=directory,
        title="Context Collector",
        id=task_id,
    )


def run_cc_exp_pl_parallel(
    root_path: str,
    directory: str,
    user_requests: List[str],
    model_provider: Literal["openai", "anthropic"] = "openai",
):
    import multiprocessing as mp
    from multiprocessing import Process

    processes = []
    num_processes = min(
        len(user_requests),
        mp.cpu_count(),
        4,
    )

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=num_processes) as executor:
        for user_request in user_requests:
            executor.submit(
                run_explorer_planner_context_collector,
                root_path=root_path,
                directory=directory,
                user_request=user_request,
                model_provider=model_provider,
            )


if __name__ == "__main__":
    main()
    # root_path = "workspace/SuperAGI"
    # directory = "workspace/SuperAGI"
    # # user_requests = [
    # #     "While creating new agents, the default tools should be the entire File Toolkit and SearX tools",
    # #     "Update the current sales engagement workflow to use SearX tool in instead of Google search tool",
    # #     "Create a new workflow to search for today’s financial news using the Searx tool, then summarize the news and "
    # #     "create a file, and then send tweets",
    # #     "Add New Relic integration to handle monitoring on APIs, Background jobs/tasks",
    # # ]

    # run_cc_exp_pl_parallel(root_path, directory, [user_requests[2]])
