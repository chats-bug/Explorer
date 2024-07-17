import os
import subprocess
import ast
from rich.console import Console

from utils.doc import Doc
from lib import logger


console = Console()


class FileUtils:
    @staticmethod
    def read_code(file_path: str, start_line: int = 1, end_line: int = 100) -> str:
        """
        Returns the formatted version of the code in the given file path.
        Appends the line numbers to the code.

        :param file_path: path to the file
        :param start_line: starting line number
        :param end_line: ending line number. If -1, reads till the end of the file
        :return:
        """

        if start_line < 1:
            start_line = 1
        if 1 < end_line < start_line:
            raise ValueError("end_line should be greater than or equal to start_line")
        if end_line < -1:
            raise ValueError("end_line should be greater than start_line or -1")

        start_line -= 1
        with open(file_path, "r") as file:
            lines = file.readlines()
            code = f"[File: {file_path} ({len(lines)} lines total)]\n"

            end_line = (
                len(lines) if (end_line > len(lines) or end_line < 0) else end_line
            )
            end_line -= 1

            if not start_line == 0:
                code += f"({len(lines) - start_line - 1} lines above)\n"
            for i in range(start_line, end_line + 1):
                code += f"{i + 1}:{lines[i]}"
            if not end_line == len(lines):
                code += f"({len(lines) - end_line - 1} lines below)\n"

        return code

    @staticmethod
    def edit_code_with_linting(
        file_path: str, start_line: int, end_line: int, new_code
    ):
        """
        Replace the code in the given file path from `start_line` to `end_line` with `new_code`.
        This function will also run the linter on the file after replacing the code.
        If the linter fails, it will revert the changes and raise an exception.

        :param file_path: path to the file
        :param start_line: starting line number
        :param end_line: ending line number
        :param new_code: new code to replace with
        :return:
        """
        with open(file_path, "r") as file:
            lines = file.readlines()

        # adjust start and end line for 0 based indexing
        start_line -= 1
        end_line -= 1

        new_lines = new_code.split("\n")
        new_lines = [f"{line}\n" for line in new_lines]

        edited_lines = lines[:start_line] + new_lines + lines[end_line + 1 :]

        # temp_file_path = (
        #     file_path.split(".", -1)[0] + "_temp." + file_path.split(".", -1)[1]
        # )
        # with open(temp_file_path, "w") as temp_file:
        #     temp_file.writelines(edited_lines)

        with open(file_path, "w") as file:
            file.writelines(edited_lines)

        try:
            lint_result = FileUtils._lint(file_path)
        except LinterException as e:
            # os.remove(temp_file_path)
            raise e

        # No syntax errors, write changes to the original file
        # with open(file_path, "w") as file:
        #     file.writelines(edited_lines)

        # # Remove temporary file and backup file
        # os.remove(temp_file_path)
        return lint_result

    @staticmethod
    def insert_code_with_linting(
        file_path: str, after_line_number: int, code: str
    ) -> str:
        """
        Insert the code in the given file path below the `line_number`.

        :param file_path: file path to insert the code
        :param after_line_number: to insert the code after this line number
        :param code: code to insert
        :return:
        """

        # adjust start and end line for 0 based indexing
        after_line_number -= 1

        with open(file_path, "r") as file:
            lines = file.readlines()
        new_lines = code.split("\n")

        new_lines = [f"{line}\n" for line in new_lines]
        edited_lines = (
            lines[: after_line_number + 1] + new_lines + lines[after_line_number + 1 :]
        )

        # temp_file_path = (
        #     file_path.split(".", -1)[0] + "_temp." + file_path.split(".", -1)[1]
        # )
        # with open(temp_file_path, "w") as temp_file:
        #     temp_file.writelines(edited_lines)

        with open(file_path, "w") as file:
            file.writelines(edited_lines)

        try:
            lint_result = FileUtils._lint(file_path)
        except LinterException as e:
            # os.remove(temp_file_path)
            raise e

        # with open(file_path, "w") as file:
        #     file.writelines(lines)

        return lint_result

    @staticmethod
    def create_code_file(file_path: str, code: str) -> str:
        """
        Create a new code file with the given code.

        :param file_path: file path to create the file
        :param code: code to write to the file
        :return:
        """
        with open(file_path, "w") as file:
            file.write(code)

        try:
            lint_result = FileUtils._lint(file_path)
        except LinterException as e:
            # os.remove(file_path)
            raise e

        return lint_result

    @staticmethod
    def _lint(file_path: str):
        lint_result = None
        # Determine the file type and run appropriate linter
        if file_path.endswith(".py"):
            # Specify the name of the conda environment you want to use
            # TODO: Manage environments in a better way
            conda_env_name = "workspace"
            python_env_name = "venv_workspace"
            # Activate the conda environment and run pylint
            command = f"source {python_env_name}/bin/activate && pylint --disable=C,R {file_path}"
            lint_result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True,
            )
        elif file_path.endswith(".js"):
            lint_result = subprocess.run(
                ["jshint", "--config", "linter_configs/jshint.json", file_path],
                capture_output=True,
                text=True,
            )
        # elif file_path.endswith(".html"):
        #     lint_result = subprocess.run(
        #         ["htmlhint", file_path], capture_output=True, text=True
        #     )
        # elif file_path.endswith(".css"):
        #     lint_result = subprocess.run(
        #         ["stylelint", file_path], capture_output=True, text=True
        #     )
        else:
            # Linting not supported for this file type
            logger.warning(
                f"Linting not supported for {file_path}. Proceeding without linting."
            )

        if lint_result:
            if lint_result.returncode != 0:
                raise LinterException(
                    return_code=lint_result.returncode,
                    stdout=lint_result.stdout,
                    stderr=lint_result.stderr,
                    file_path=file_path,
                )
            return lint_result.stdout

        return None


class LinterException(Exception):
    """
    Should have the following properties:
    - message: str
    - file_path: str
    - file_extension: str
    """

    def __init__(self, return_code, stdout, stderr, file_path):
        self.return_code = return_code
        self.stdout = stdout.strip()
        if stderr:
            stderr = stderr.strip()
            stderr = None if stderr == "" else stderr
        self.stderr = stderr
        self.message = f"[stdout]:{stdout.strip()}"
        if stderr:
            self.message += f"\n\n[stderr]:{stderr}"
        self.file_path = file_path
        super().__init__(self.message)

    def __str__(self):
        return f"[File: {self.file_path} (Return Code {self.return_code})]\n\n{self.message}"


class ASTOutlineVisitor(ast.NodeVisitor):
    def __init__(self):
        self.tree = {}

    def visit_Module(self, node):
        self.generic_visit(node)
        return self.tree

    def visit_ClassDef(self, node):
        class_name = node.name
        self.tree[class_name] = {
            "type": "class",
            "body": {},
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
        }
        class_body_visitor = ASTOutlineVisitor()
        class_body_visitor.visit(node)
        self.tree[class_name]["body"] = class_body_visitor.tree
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        func_name = node.name
        self.tree[func_name] = {
            "type": "function",
            "body": {},
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
        }
        func_body_visitor = ASTOutlineVisitor()
        func_body_visitor.visit(node)
        self.tree[func_name]["body"] = func_body_visitor.tree
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                self.tree[var_name] = {
                    "type": "variable",
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno,
                }
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            self.tree[var_name] = {
                "type": "variable",
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
            }
        self.generic_visit(node)


def generate_outline_tree(code):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if not hasattr(node, "end_lineno"):
            node.end_lineno = node.lineno
    visitor = ASTOutlineVisitor()
    outline_tree = visitor.visit(tree)
    return outline_tree


def generate_outline(doc: Doc):
    if doc is None:
        return {}

    # check is doc.path is a file or a directory
    if not os.path.isfile(doc.path):
        return {}

    # check if the file is a python file
    if not doc.path.endswith(".py"):
        return {}

    # now get all the classes and functions in the file
    # along with the docstring, signature, and line number
    with open(doc.path, "r") as f:
        source_code = f.read()

    # Parse the source code into AST.
    tree = ast.parse(source_code)

    # Initialize the store for extracted information.
    accumulated = {"class": [], "function": [], "variable": []}
    extract_info(tree, accumulated)

    return accumulated


def extract_info(node, accumulated):
    """Recursively extract info from AST nodes."""
    if isinstance(node, ast.ClassDef):
        accumulated["class"].append(
            {
                "name": node.name,
                "methods": [
                    method.name
                    for method in node.body
                    if isinstance(method, ast.FunctionDef)
                ],
                "docstring": ast.get_docstring(node),
                "returns": None,  # Classes do not have return types.
                "line_nos": (node.lineno, node.end_lineno),
            }
        )
    elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        accumulated["function"].append(
            {
                "name": node.name,
                "arguments": [arg.arg for arg in node.args.args],
                "docstring": ast.get_docstring(node),
                "returns": (
                    "None or not specified"
                    if node.returns is None
                    else ast.dump(node.returns)
                ),
                "line_nos": (node.lineno, node.end_lineno),
            }
        )
    elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        accumulated["variable"].append(
            {
                "name": node.targets[0].id,
                "type": None if node.value is None else node.value.__class__.__name__,
                "line_nos": (node.lineno, node.end_lineno),
            }
        )

    # Recursively continue for child nodes.
    for child in ast.iter_child_nodes(node):
        extract_info(child, accumulated)
