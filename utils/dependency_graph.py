import ast
import os
import pickle
import sys
import json
import questionary
import networkx as nx
import importlib.util
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from lib import logger
from config import console
from tools import LSPRequestTypes, LSPUtils, LSPSupportedLanguages


lsp_tool = LSPUtils(
    language=LSPSupportedLanguages.PYTHON,
    repo_path=os.path.abspath(""),
    file_path=os.path.abspath(""),
    line_number=1,
    request_type=LSPRequestTypes.DEFINITION,
)


def is_repo_module(
    module_name: str, current_file_path: str, root_path: Optional[str] = None
) -> bool:
    current_dir = os.path.dirname(os.path.abspath(current_file_path))
    repo_root = root_path or find_repo_root(current_dir)
    logger.debug(
        f"🔵 Module Name: {module_name}; Repo root: {repo_root}; Current dir: {current_dir}"
    )

    if repo_root is None:
        return False

    module_parts = module_name.split(".")
    for i in range(len(module_parts), 0, -1):
        partial_path_1 = os.path.join(repo_root, *module_parts[:i])
        partial_path_2 = os.path.join(current_dir, *module_parts[:i])
        logger.debug(f"🔵 Partial path: {partial_path_1}, {partial_path_2}")

        # Check for .py file
        if os.path.isfile(partial_path_1 + ".py") or os.path.isfile(
            partial_path_2 + ".py"
        ):
            return True

        # Check for directory with __init__.py
        if os.path.isdir(partial_path_1) and os.path.isfile(
            os.path.join(partial_path_1, "__init__.py")
        ):
            return True

        if os.path.isdir(partial_path_2) and os.path.isfile(
            os.path.join(partial_path_2, "__init__.py")
        ):
            return True

    return False


def find_repo_root(start_path: str) -> str:
    current_path = start_path
    while current_path != os.path.dirname(current_path):  # Stop at filesystem root
        if os.path.exists(os.path.join(current_path, ".git")):
            return current_path
        current_path = os.path.dirname(current_path)
    return None


def is_python_package(module_name: str) -> bool:
    try:
        # Try to find the module spec
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            return True

        # If spec is None, try to import the module
        __import__(module_name)
        return True
    except ImportError:
        return False


def categorize_import(
    module_name: str,
    imports: Optional[List[Tuple[str, str]]],
    current_file_path: str,
    line_no: int,
    repo_modules: Dict[str, List[str]],
    python_packages: Dict[str, List[str]],
    root_path: Optional[str] = None,
):
    # check if module name has 'as' in it
    module_name_without_as = module_name.split(" as ")[0]
    if is_repo_module(module_name_without_as, current_file_path, root_path):
        if module_name not in repo_modules:
            repo_modules[module_name] = {"imports": [], "line_no": line_no}
        if imports:
            repo_modules[module_name]["imports"].extend(imports)
    else:
        # does not really matter then
        ...


def get_imports(path: str, root_path: Optional[str] = None):
    if not path.endswith(".py"):
        return {}, {}

    with open(path, "r") as f:
        tree = ast.parse(f.read())

    repo_modules = {}
    python_packages = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                line_no = alias.lineno
                import_name = (
                    f"{module_name} as {alias.asname}" if alias.asname else module_name
                )
                logger.debug(
                    f"⭕️ Module name: {module_name}; Import name: {import_name}; Line no: {line_no}"
                )
                categorize_import(
                    module_name=import_name,
                    imports=None,
                    current_file_path=path,
                    line_no=line_no,
                    repo_modules=repo_modules,
                    python_packages=python_packages,
                    root_path=root_path,
                )
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            if module_name:
                imports = [(alias.name, alias.asname) for alias in node.names]
                logger.debug(
                    f"🟠 Module name: {module_name}; Imports: {imports}; Line no: {node.lineno}"
                )
                categorize_import(
                    module_name=module_name,
                    imports=imports,
                    current_file_path=path,
                    line_no=node.lineno,
                    repo_modules=repo_modules,
                    python_packages=python_packages,
                    root_path=root_path,
                )

    return repo_modules, python_packages


def build_call_graph(entry_point: str, base_path: str) -> nx.DiGraph:
    G = nx.DiGraph()
    visited = set()
    # make sure base path is an absolute path
    base_path = os.path.abspath(base_path)

    def process_file(file_path: str, level=0):
        if file_path in visited:
            return

        visited.add(file_path)
        relative_path = os.path.relpath(file_path, base_path)
        G.add_node(relative_path)

        repo_modules, _ = get_imports(file_path, base_path)
        # if repo_modules:
        #     logger.info(f"[bold green] PROCESSING: [/] {file_path} // {base_path}")
        if not repo_modules:
            logger.info(f"[bold red] NO MODULES: [/] {file_path} // {base_path}")
        for module_name, import_dict in repo_modules.items():
            # TODO: Extend to handle other languages as well
            lsp_tool.file_path = file_path
            lsp_tool.language = LSPSupportedLanguages.PYTHON
            lsp_tool.line_number = import_dict["line_no"]
            lsp_tool.symbol = None
            with open(file_path, "r") as f:
                lines = f.readlines()
                module_import_line = lines[lsp_tool.line_number - 1]
                # get the starting index of the module_name
                module_name_starting_index = module_import_line.index(module_name)
                # we are interested in the idx number of the last "." in the module_name
                if "." in module_name:
                    lsp_tool.column_number = (
                        module_name_starting_index + module_name.rindex(".") + 1
                    )
                else:
                    lsp_tool.column_number = module_name_starting_index

            lsp_tool.request_type = LSPRequestTypes.DEFINITION
            lsp_result = lsp_tool.run()
            # logger.info(
            #     f"[bold gray10]FETCH DEFINITION[/]: {module_name} ; Level ({level}); LSP Result: {lsp_result['success']}"
            # )
            if lsp_result["success"]:
                node = os.path.relpath(
                    lsp_result["response"][0]["absolutePath"], base_path
                )
                G.add_node(node)
                G.add_edge(
                    relative_path,
                    node,
                    imports=import_dict["imports"],
                )
                logger.info(
                    f"EDGE: {relative_path} -> {node} [{import_dict['imports']}]"
                )
                process_file(lsp_result["response"][0]["absolutePath"], level=level + 1)

    process_file(os.path.abspath(entry_point))
    return G


def navigate_dependencies():
    entry_point = questionary.path(
        "Enter the path to the Python file to start from:"
    ).ask()
    base_path = os.path.dirname(os.path.abspath(entry_point))

    G = build_call_graph(entry_point, base_path)
    visualize_graph_plotly(G)

    current_file = os.path.relpath(entry_point, base_path)
    journey = [current_file]

    while True:
        questionary.print(f"Current file: {current_file}")
        dependencies = list(G.successors(current_file))

        if not dependencies:
            questionary.print("This file has no further dependencies.")
            break

        choices = []
        for i, dep in enumerate(dependencies, 1):
            edge_data = G.get_edge_data(current_file, dep)
            imports = ", ".join(edge_data["imports"]) if edge_data else "No imports"
            choices.append(f"{i}. {dep} (imports: {imports})")

        choice = questionary.select(
            "Choose the next file to explore:",
            choices,
            pointer="👉",
            use_indicator=True,
            style=questionary.Style([("highlighted", "fg:#FF9D00 bold reverse")]),
        ).ask()
        choice = choice.split(".")[0]

        # if choice.lower() == "q":
        #     break

        try:
            index = int(choice) - 1
            if 0 <= index < len(dependencies):
                current_file = dependencies[index]
                journey.append(current_file)
            else:
                questionary.print("Invalid choice. Please try again.")
        except ValueError:
            questionary.print("Invalid input. Please enter a number or 'q'.")

    questionary.print("\nYour journey:")
    questionary.print(" -> ".join(journey))


if __name__ == "__main__":
    # navigate_dependencies()
    entry_point = "main.py"
    base_path = os.path.abspath(".")
    G = build_call_graph(entry_point=entry_point, base_path=base_path)
    console.print(G.nodes())
    # visualize_graph_plotly(G)

    # os.makedirs(
    #     f"saved_states/call_graphs/{entry_point.split('/', -1)[0]}", exist_ok=True
    # )
    with open(f"saved_states/call_graphs/ex_main_py.gpickle", "wb") as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

    # entry_point = "workspace/todo/website/__init__.py"
    # base_path = "workspace/todo/"
    # repo_modules, python_packages = get_imports(entry_point, base_path)
    # console.print(repo_modules)
    # console.print(python_packages)
