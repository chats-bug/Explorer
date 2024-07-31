import json
import os
import pyvis.network as net
import pickle
import questionary

from agents.PlannerAgent.tools.update_plan import Task
from config import config, console
from lib import logger


def visualize_graph():
    graph_pickle_path = questionary.path(
        "Enter the path to the graph pickle file:"
    ).ask()
    if graph_pickle_path.strip() == "":
        graph_pickle_path = "saved_states/call_graphs/todo_main_py.gpickle"
        logger.warning(f"Using default graph pickle path: {graph_pickle_path}")

    with open(graph_pickle_path, "rb") as f:
        G = pickle.load(f)

    network = net.Network(
        directed=True,
        notebook=True,
        height="800px",
        bgcolor="#1b1636",
        font_color="#4EC9B0",
        select_menu=True,
        filter_menu=True,
        # layout=True,
        neighborhood_highlight=True,
    )
    network.from_nx(G)
    network.show_buttons(filter_="physics")

    network.show("call_graph.html")
    logger.info("Call graph visualization saved as call_graph.html")


def test_coding_agent():
    from agents.CodingAgent.agent import CodingAgent
    import subprocess

    # call the shell script to load from backup
    # use subprocess to call the shell script
    load_from_backup_script_path = "scripts/load_from_backup.sh"
    backup_dir_name = "SuperAGI"
    subprocess.run(["sh", load_from_backup_script_path, backup_dir_name])

    logger.info(
        f"Backed up from workspace/backup/{backup_dir_name} to workspace/{backup_dir_name}"
    )
    console.print("\n")

    reddit_problem_statement = "Make a new tool in SuperAGI called RedditSurfer. This tool will take in a single query and search reddit, summarize the top 5 posts using gpt-3.5-turbo and then return the summarized version. The reddit post api to do so is 'api.reddit.com/search/{query}'."
    finance_workflow_problem_statement = "Create a new workflow to search for today's financial news using the Searx tool, then summarize the news and create a file, and then send tweets"
    new_relic_problem_statement = (
        "Add New Relic integration to handle monitoring on APIs, Background jobs/tasks"
    )
    replace_google_problem_statement = "Update the current sales engagement workflow to use SearX tool in instead of Google search tool"
    teams_table_problem_statement = "Add a new table teams and write controller layer and models and handle authentication and authorization well"

    reddit_tool_plan = [
        {
            "step": 1,
            "task_description": "Create a schema for the RedditSurfer tool.",
            "create": [
                "workspace/SuperAGI/superagi/tools/reddit_surfer/reddit_surfer.py"
            ],
            "update": [],
            "update_info": "Create a class 'RedditSurferSchema' extending BaseModel with a single field 'query' of type string.",
            "reference": [
                "workspace/SuperAGI/superagi/tools/google_serp_search/google_serp_search.py"
            ],
            "reference_info": "Refer to GoogleSerpSchema for structure.",
        },
        {
            "step": 2,
            "task_description": "Implement the RedditSurfer tool class by extending BaseTool.",
            "create": [],
            "update": [
                "workspace/SuperAGI/superagi/tools/reddit_surfer/reddit_surfer.py"
            ],
            "update_info": "Create a class 'RedditSurferTool' extending BaseTool with necessary attributes and methods.",
            "reference": [
                "workspace/SuperAGI/superagi/tools/google_serp_search/google_serp_search.py"
            ],
            "reference_info": "Refer to GoogleSerpTool for structure and methods.",
        },
        {
            "step": 3,
            "task_description": "Create a wrapper for the Reddit API to handle search queries.",
            "create": ["workspace/SuperAGI/superagi/helper/reddit_api.py"],
            "update": [],
            "update_info": "Create a class 'RedditApiWrap' with methods to interact with the Reddit API.",
            "reference": ["workspace/SuperAGI/superagi/helper/google_serp.py"],
            "reference_info": "Refer to GoogleSerpApiWrap for structure and methods.",
        },
        {
            "step": 4,
            "task_description": "Integrate GPT-3.5-turbo for summarizing Reddit posts.",
            "create": [],
            "update": [
                "workspace/SuperAGI/superagi/tools/reddit_surfer/reddit_surfer.py"
            ],
            "update_info": "Implement summarization using GPT-3.5-turbo in the 'RedditSurferTool' class.",
            "reference": ["workspace/SuperAGI/superagi/llms/openai.py"],
            "reference_info": "Refer to OpenAi class for integration.",
        },
        {
            "step": 5,
            "task_description": "Implement error handling for the RedditSurfer tool.",
            "create": [],
            "update": [
                "workspace/SuperAGI/superagi/tools/reddit_surfer/reddit_surfer.py"
            ],
            "update_info": "Add error handling in the 'RedditSurferTool' class.",
            "reference": ["workspace/SuperAGI/superagi/helper/error_handler.py"],
            "reference_info": "Refer to ErrorHandler class for structure.",
        },
        {
            "step": 6,
            "task_description": "Write unit tests for the RedditSurfer tool.",
            "create": ["workspace/SuperAGI/tests/tools/reddit_surfer_test.py"],
            "update": [],
            "update_info": "Write unit tests for the 'RedditSurferTool' class.",
            "reference": [
                "workspace/SuperAGI/tests/tools/google_calendar/create_event_test.py"
            ],
            "reference_info": "Refer to Google Calendar tool tests for structure.",
        },
    ]
    finance_workflow_plan = [
        {
            "step": 1,
            "task": "Define a new workflow in `workflow_seed.py` to search for today's financial news using the Searx tool, summarize it, create a file, and send tweets.",
            "create": [],
            "update": ["workspace/SuperAGI/superagi/agent/workflow_seed.py"],
            "update_info": "Add a new method `build_financial_news_workflow` in `workflow_seed.py` that defines the steps for the new workflow.",
            "reference": ["workspace/SuperAGI/superagi/agent/workflow_seed.py"],
            "reference_info": "Refer to the existing workflow methods such as `build_sales_workflow` and `build_recruitment_workflow` for structure and implementation details.",
        },
        {
            "step": 2,
            "task": "Implement the step to search for today's financial news using the Searx tool.",
            "create": [],
            "update": ["workspace/SuperAGI/superagi/agent/workflow_seed.py"],
            "update_info": "Add a step in the `build_financial_news_workflow` method to use the `SearxSearchTool` for searching today's financial news.",
            "reference": [
                "workspace/SuperAGI/superagi/tools/searx/searx.py",
                "workspace/SuperAGI/superagi/agent/workflow_seed.py",
            ],
            "reference_info": "Refer to the `SearxSearchTool` implementation in `searx.py`.",
        },
        {
            "step": 3,
            "task": "Implement the step to summarize the search results.",
            "create": [],
            "update": ["workspace/SuperAGI/superagi/agent/workflow_seed.py"],
            "update_info": "Add a step in the `build_financial_news_workflow` method to summarize the search results using the `ResourceSummarizer`.",
            "reference": [
                "workspace/SuperAGI/superagi/resource_manager/resource_summary.py",
                "workspace/SuperAGI/superagi/agent/workflow_seed.py",
            ],
            "reference_info": "Refer to the `ResourceSummarizer` implementation in `resource_summary.py`.",
        },
        {
            "step": 4,
            "task": "Implement the step to create a file with the summarized news.",
            "create": [],
            "update": ["workspace/SuperAGI/superagi/agent/workflow_seed.py"],
            "update_info": "Add a step in the `build_financial_news_workflow` method to create a file with the summarized news using the `ResourceManager`.",
            "reference": [
                "workspace/SuperAGI/superagi/resource_manager/resource_manager.py",
                "workspace/SuperAGI/superagi/agent/workflow_seed.py",
            ],
            "reference_info": "Refer to the `ResourceManager` implementation in `resource_manager.py`.",
        },
        {
            "step": 5,
            "task": "Implement the step to send tweets with the summarized news.",
            "create": [],
            "update": ["workspace/SuperAGI/superagi/agent/workflow_seed.py"],
            "update_info": "Add a step in the `build_financial_news_workflow` method to send tweets with the summarized news using the `SendTweetsTool`.",
            "reference": [
                "workspace/SuperAGI/superagi/tools/twitter/send_tweets.py",
                "workspace/SuperAGI/superagi/agent/workflow_seed.py",
            ],
            "reference_info": "Refer to the `SendTweetsTool` implementation in `send_tweets.py`.",
        },
    ]
    new_relic_plan = [
        {
            "step": 1,
            "task": "Install New Relic Python Agent",
            "create": [],
            "update": ["workspace/SuperAGI/requirements.txt"],
            "update_info": "Add `newrelic` to the list of dependencies in `requirements.txt`.",
            "reference": [],
            "reference_info": "",
        },
        {
            "step": 2,
            "task": "Update Configuration",
            "create": [],
            "update": [
                "workspace/SuperAGI/config_template.yaml",
                "workspace/SuperAGI/superagi/config/config.py",
            ],
            "update_info": "Add New Relic configuration settings to `config_template.yaml` and ensure they are loaded correctly in `config.py`.",
            "reference": [
                "workspace/SuperAGI/config_template.yaml",
                "workspace/SuperAGI/superagi/config/config.py",
            ],
            "reference_info": "Add `NEW_RELIC_LICENSE_KEY` and `NEW_RELIC_APP_NAME` to `config_template.yaml`. Update `config.py` to read these settings.",
        },
        {
            "step": 3,
            "task": "Initialize New Relic in FastAPI",
            "create": [],
            "update": ["workspace/SuperAGI/main.py"],
            "update_info": "Import and initialize the New Relic agent in `main.py`.",
            "reference": ["workspace/SuperAGI/main.py"],
            "reference_info": "Add `import newrelic.agent` and initialize with `newrelic.agent.initialize()` at the beginning of the file.",
        },
        {
            "step": 4,
            "task": "Monitor FastAPI Endpoints",
            "create": [],
            "update": ["workspace/SuperAGI/main.py"],
            "update_info": "Ensure FastAPI endpoints are monitored by New Relic.",
            "reference": ["workspace/SuperAGI/main.py"],
            "reference_info": "Add necessary New Relic decorators or middleware to monitor FastAPI endpoints.",
        },
        {
            "step": 5,
            "task": "Monitor Celery Tasks",
            "create": [],
            "update": ["workspace/SuperAGI/superagi/worker.py"],
            "update_info": "Modify `worker.py` to include New Relic monitoring for Celery tasks.",
            "reference": ["workspace/SuperAGI/superagi/worker.py"],
            "reference_info": "Add `import newrelic.agent` and initialize with `newrelic.agent.initialize()` at the beginning of the file. Use New Relic's Celery instrumentation to monitor tasks.",
        },
    ]
    replace_google_plan = [
        {
            "step": 1,
            "task": "Replace usage of GoogleSearchTool with SearxSearchTool in the sales engagement workflow.",
            "create": [],
            "update": ["workspace/SuperAGI/superagi/agent/workflow_seed.py"],
            "update_info": "Replace `GoogleSearchTool` with `SearxSearchTool` in `step5` of the `build_sales_workflow` method.",
            "reference": ["workspace/SuperAGI/superagi/agent/workflow_seed.py"],
            "reference_info": "GoogleSearchTool is used in `step5` of the `build_sales_workflow` method.",
        },
        {
            "step": 2,
            "task": "Update configuration settings in config_template.yaml.",
            "create": [],
            "update": ["workspace/SuperAGI/config_template.yaml"],
            "update_info": "Remove `GOOGLE_API_KEY` and `SEARCH_ENGINE_ID` if they are no longer needed.",
            "reference": [
                "workspace/SuperAGI/config_template.yaml",
                "workspace/SuperAGI/superagi/tools/google_search/google_search.py",
            ],
            "reference_info": "Configuration settings for the Google search tool are specified under `GOOGLE_API_KEY` and `SEARCH_ENGINE_ID` in `config_template.yaml`. These keys are used in the `GoogleSearchTool` class in `google_search.py`.",
        },
    ]
    teams_model_plan = [
        {
            "step": 1,
            "task": "Create a new model file for the teams table",
            "create": [
                "workspace/SuperAGI/superagi/models/team.py"
            ],
            "update": [],
            "update_info": "Define the Team model with appropriate fields such as id, name, description, and organisation_id. Use SQLAlchemy ORM to define the model.",
            "reference": [
                "workspace/SuperAGI/superagi/models/base_model.py",
                "workspace/SuperAGI/superagi/models/organisation.py"
            ],
            "reference_info": "Use DBBaseModel as the base class and reference the Organisation model for the relationship."
        },
        {
            "step": 2,
            "task": "Create a new association table for the many-to-many relationship between users and teams",
            "create": [
                "workspace/SuperAGI/superagi/models/user_team.py"
            ],
            "update": [],
            "update_info": "Define the UserTeam association table with user_id and team_id as foreign keys.",
            "reference": [
                "workspace/SuperAGI/superagi/models/base_model.py"
            ],
            "reference_info": "Use DBBaseModel as the base class and reference both User and Team models for the relationships."
        },
        {
            "step": 3,
            "task": "Update the __init__.py file in the models directory to import the new Team and UserTeam models",
            "create": [],
            "update": [
                "workspace/SuperAGI/superagi/models/__init__.py"
            ],
            "update_info": "Add import statements for the new Team and UserTeam models.",
            "reference": [],
            "reference_info": ""
        },
        {
            "step": 4,
            "task": "Create a new controller file for team-related API endpoints",
            "create": [
                "workspace/SuperAGI/superagi/controllers/team.py"
            ],
            "update": [],
            "update_info": "Implement CRUD operations for teams, including create_team, get_team, update_team, delete_team, add_user_to_team, and remove_user_from_team functions.",
            "reference": [
                "workspace/SuperAGI/superagi/controllers/user.py",
                "workspace/SuperAGI/superagi/controllers/agent.py"
            ],
            "reference_info": "Use similar structure and authentication methods as in the user and agent controllers."
        },
        {
            "step": 5,
            "task": "Update the main.py file to include the new team router",
            "create": [],
            "update": [
                "workspace/SuperAGI/main.py"
            ],
            "update_info": "Import the team router and add it to the FastAPI app with an appropriate prefix.",
            "reference": [],
            "reference_info": ""
        },
        {
            "step": 6,
            "task": "Implement authentication and authorization for team-related operations",
            "create": [],
            "update": [
                "workspace/SuperAGI/superagi/helper/auth.py"
            ],
            "update_info": "Add functions to check if a user has permissions to perform operations on a team, including team membership checks.",
            "reference": [
                "workspace/SuperAGI/superagi/helper/auth.py"
            ],
            "reference_info": "Use similar methods as existing authentication functions, but tailored for team operations."
        },
        {
            "step": 7,
            "task": "Update the User model to include a relationship with teams",
            "create": [],
            "update": [
                "workspace/SuperAGI/superagi/models/user.py"
            ],
            "update_info": "Add a many-to-many relationship between User and Team models using the UserTeam association table.",
            "reference": [
                "workspace/SuperAGI/superagi/models/organisation.py"
            ],
            "reference_info": "Reference how the relationship between User and Organisation is defined, but use a many-to-many relationship instead."
        },
        {
            "step": 8,
            "task": "Update the Team model to include a relationship with users",
            "create": [],
            "update": [
                "workspace/SuperAGI/superagi/models/team.py"
            ],
            "update_info": "Add a many-to-many relationship between Team and User models using the UserTeam association table.",
            "reference": [
                "workspace/SuperAGI/superagi/models/organisation.py"
            ],
            "reference_info": "Reference how the relationship between Organisation and User is defined, but use a many-to-many relationship instead."
        },
        {
            "step": 9,
            "task": "Create a new Alembic migration script for the database schema changes",
            "create": [
                "workspace/SuperAGI/migrations/versions/create_teams_and_user_team_tables.py"
            ],
            "update": [],
            "update_info": "Use Alembic to generate a new migration script that creates the teams table, user_team association table, and updates the users table if necessary.",
            "reference": [
                "workspace/SuperAGI/migrations/versions/"
            ],
            "reference_info": "Reference existing migration scripts to understand the structure and use of Alembic for schema changes."
        },
        {
            "step": 10,
            "task": "Update API documentation to include new team-related endpoints",
            "create": [],
            "update": [
                "workspace/SuperAGI/README.MD"
            ],
            "update_info": "Add documentation for the new team-related API endpoints, including their routes, request/response formats, and any authentication requirements.",
            "reference": [
                "workspace/SuperAGI/README.MD"
            ],
            "reference_info": "Reference existing API documentation to maintain consistency in format and style."
        },
        {
            "step": 11,
            "task": "Create unit tests for the new Team model and controller",
            "create": [
                "workspace/SuperAGI/tests/unit_tests/models/test_team.py",
                "workspace/SuperAGI/tests/unit_tests/controllers/test_team.py"
            ],
            "update": [],
            "update_info": "Implement unit tests for the Team model and team controller, covering CRUD operations, relationships, and authorization checks.",
            "reference": [
                "workspace/SuperAGI/tests/unit_tests/models/test_user.py",
                "workspace/SuperAGI/tests/unit_tests/controllers/test_user.py"
            ],
            "reference_info": "Reference existing unit tests for the User model and controller to maintain consistency in testing approach and coverage."
        },
        {
            "step": 12,
            "task": "Create integration tests for team-related operations",
            "create": [
                "workspace/SuperAGI/tests/integration_tests/test_team_integration.py"
            ],
            "update": [],
            "update_info": "Implement integration tests that cover the interaction between teams, users, and other components of the system. Include tests for team creation, user assignment, and authorization in the context of other operations.",
            "reference": [
                "workspace/SuperAGI/tests/integration_tests/"
            ],
            "reference_info": "Reference existing integration tests to understand the structure and approach used for testing component interactions."
        },
        {
            "step": 13,
            "task": "Review and update related components",
            "create": [],
            "update": [
                "workspace/SuperAGI/superagi/models/project.py",
                "workspace/SuperAGI/superagi/models/organisation.py",
                "workspace/SuperAGI/superagi/controllers/project.py",
                "workspace/SuperAGI/superagi/controllers/organisation.py"
            ],
            "update_info": "Review and update the Project and Organisation models and controllers to incorporate team-related functionality if necessary. This may include adding team-related fields, methods, or API endpoints.",
            "reference": [
                "workspace/SuperAGI/superagi/models/team.py",
                "workspace/SuperAGI/superagi/controllers/team.py"
            ],
            "reference_info": "Reference the newly created Team model and controller to ensure consistency in how teams are handled across the application."
        }
    ]

    from agents.CoreLoopDeveloper.agent import CoreLoopDeveloperAgent

    task_id = "teams_model_plan_task"

    core_loop_agent = CoreLoopDeveloperAgent(
        title="Core loop developer",
        max_retries=5,
        max_iters=50,
        model_provider="openai",
    )
    existing_files = set()
    responses = []
    for i, plan in enumerate(teams_model_plan):
        user_input = f"Global Objective: {teams_table_problem_statement}\nCurrent Plan: {json.dumps(plan, indent=4)}"
        # user_input = f"Current Plan: {json.dumps(plan, indent=4)}"

        response = core_loop_agent.run(
            user_input=user_input,
            file_list=list(
                set(list(existing_files) + plan["update"] + plan["reference"])
            ),
            prev_changes="\n----\n".join(responses),
        )
        os.makedirs(f"saved_states/core_loop/{task_id}", exist_ok=True)
        with open(f"saved_states/core_loop/{task_id}/step_{i+1}.txt", "w") as f:
            f.write(response)
        responses.append(response)

        console.print("\n\n")

        logger.info(f"Finish response: {response}\n")
        console.input("Press Enter to continue...\n")
        existing_files.update(plan["create"] + plan["update"])

    # coding_agent_instance = CodingAgent(
    #     title="RedditSurfer Tool Coding agent",
    #     task_id="reddit_unique_task",
    #     max_retries=5,
    #     model_provider="openai",
    # )
    # coding_agent_instance.run(plan=[Task(**k) for k in reddit_tool_plan])

    # from agents.CodingAgent.simple_agent import CodeWriter

    # simple_coding_agent = CodeWriter(
    #     title="RedditSurfer Tool Coding agent",
    #     max_retries=5,
    #     max_iters=50,
    #     model_provider="openai",
    # )
    # # make a set of existing files
    # existing_files = set()
    # for plan in reddit_tool_plan:
    #     finish_response = simple_coding_agent.run(
    #         objective=f"Global Objective: {original_problem_statement}\nCurrent Task: {plan['task_description']}",
    #         existing_files=list(
    #             set(list(existing_files) + plan["update"] + plan["reference"])
    #         ),
    #         context=plan["update_info"] + "\n\n" + plan["reference_info"],
    #         new_files=plan["create"],
    #     )
    #     console.print("\n\n")

    #     logger.info(f"Finish response: {finish_response}")
    #     console.input("Press Enter to continue...")
    #     existing_files.update(plan["create"] + plan["update"])


test_coding_agent()
