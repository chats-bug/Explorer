import os
import concurrent.futures
from gitignore_parser import parse_gitignore
from typing import Dict, Any, Optional
from rich.console import Console

from utils.doc.doc_model import Doc
from lib import logger
from config import console


def read_file(file_name):
    try:
        with open(file_name, "r") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file: {file_name}")
        raise Exception(e)


class DocUtils:
    def __init__(self, path: str, gitignore_path: str = None, use_default_gitignore: bool = True):
        self.documentation_file_level_system_prompt = "documentation_system_prompt.txt"
        self.documentation_file_level_user_prompt = "documentation_user_prompt.txt"

        self.documentation_folder_level_system_prompt = (
            "documentation_system_prompt_folder.txt"
        )
        self.documentation_folder_level_user_prompt = (
            "documentation_user_folder_prompt.txt"
        )

        self.root_doc = Doc(
            path=path, parent=None, children=[], documentation="", summary=""
        )
        if gitignore_path and os.path.exists(gitignore_path):
            self.matches = parse_gitignore(gitignore_path)
        elif use_default_gitignore:
            self.matches = parse_gitignore("workspace/.gitignore")
        else:
            self.matches = lambda x: False

        self.ignore_file_types = [".png", ".pdf", ".ico", ".jpg", ".jpeg", ".pfb", ".ttf", ".tif", ".dvi", ".npz", ".db"]

    def _list_files_and_folders(self, filepath):

        files = []
        folders = []
        for element in os.listdir(filepath):
            element_starts_with_dot = element.startswith(".")
            element_in_gitignore = self.matches(os.path.join(filepath, element))
            element_ends_with_ignore_file_types = element.endswith(tuple(self.ignore_file_types))

            if element_starts_with_dot or element_in_gitignore or element_ends_with_ignore_file_types:
                logger.warning(
                    f"[bold red]Ignoring[/bold red]: [File: ({os.path.join(filepath, element)})]."
                )
                continue
            if os.path.isfile(os.path.join(filepath, element)):
                try:
                    read_file(os.path.join(filepath, element))
                except Exception as e:
                    ext = os.path.splitext(element)[1]
                    self.ignore_file_types.append(ext)
                    logger.warning(
                        f"[bold red]Ignoring[/bold red]: [File: ({os.path.join(filepath, element)})]. Adding {ext} to ignore list"
                    )
                    continue
                files.append(os.path.join(filepath, element))
            elif os.path.isdir(os.path.join(filepath, element)):
                folders.append(os.path.join(filepath, element))
        return files, folders

    def _extract_documentation(self, text):
        # FIXME: Hack to skip documentation. Remove this.
        if not text:
            return ""
        return text.split("# Documentation")[1].split("# Summary")[0].strip()

    def _extract_summary(self, text):
        # FIXME: Hack to skip summary. Remove this.
        if not text:
            return ""
        return text.split("# Summary")[1].strip()

    def _generate_documentation_for_folder(
            self, folder_path: str, documentations: list
    ):
        # generate documentation for the folder
        logger.debug("Generating documentation for folder:", folder_path)
        # system_prompt = self.get_prompt(self.documentation_folder_level_system_prompt)
        # user_prompt = self.get_prompt(self.documentation_folder_level_user_prompt)
        # user_prompt = user_prompt.format(
        #     folder_path=folder_path, documentation="\n".join(documentations)
        # )

        # FIXME: Temporarily disabling the model
        # response = self.model.chat_completion(
        #     [
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt},
        #     ]
        # )
        # return response, folder_path
        return None, folder_path

    def _generate_documentation_for_file(self, code, filename):
        if not filename.endswith((".py", ".sh", ".css", ".html", ".js", ".txt", ".md")):
            return (
                f"# Documentation {filename} - Asset File # Summary {filename} - Asset File",
                filename,
            )
        logger.debug("Generating documentation for file:", filename)
        # system_prompt = self.get_prompt(self.documentation_file_level_system_prompt)
        # user_prompt = self.get_prompt(self.documentation_file_level_user_prompt)
        # user_prompt = user_prompt.format(code=code, filename=filename)

        # FIXME: Temporarily disabling the model
        # response = self.model.chat_completion(
        #     [
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt},
        #     ]
        # )
        # return response, filename
        return None, filename

    def generate_documentation(self, parent_node):
        files, folders = self._list_files_and_folders(parent_node.path)

        # generate the documentation for the files parallely
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(
                    self._generate_documentation_for_file, read_file(file), file
                ): file
                for file in files
            }
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    response, filename = future.result()
                    documentation = self._extract_documentation(response)
                    summary = self._extract_summary(response)
                    parent_node.children.append(
                        Doc(
                            path=filename,
                            children=[],
                            documentation=documentation,
                            summary=summary,
                        )
                    )
                except Exception as exc:
                    console.print_exception(show_locals=True)

        for folder in folders:
            doc_for_folder = Doc(path=folder, children=[], documentation="", summary="")
            parent_node.children.append(doc_for_folder)
            self.generate_documentation(doc_for_folder)

        response, folder_name = self._generate_documentation_for_folder(
            parent_node.path, parent_node.get_documentation_from_children()
        )
        parent_node.documentation = self._extract_documentation(response)
        parent_node.summary = self._extract_summary(response)

    def generate_documentation_json(self) -> Dict[str, Any]:
        return self.root_doc.get_dict()

    def update_documentation(
            self, root_doc: Doc, file_path: str, is_file_exists: bool = True
    ) -> Doc:

        # Find the doc in the tree
        doc = self._find_doc(root_doc, os.path.dirname(file_path))
        if not doc:
            raise FileNotFoundError("Doc for the directory not found in the tree")

        if is_file_exists:
            # find the relevant
            update_doc = None
            for child in doc.children:
                if child.path == file_path:
                    update_doc = child
                    break

            if not update_doc:
                raise FileNotFoundError("Doc for the file not found in the tree")

            with open(file_path, "r") as file:
                code = file.read()
            response, _ = self._generate_documentation_for_file(code, file_path)
            update_doc.documentation = self._extract_documentation(response)
            update_doc.summary = self._extract_summary(response)
        else:
            with open(file_path, "r") as file:
                code = file.read()
            response, _ = self._generate_documentation_for_file(code, file_path)
            documentation = self._extract_documentation(response)
            summary = self._extract_summary(response)
            doc.children.append(
                Doc(
                    path=file_path,
                    children=[],
                    documentation=documentation,
                    summary=summary,
                )
            )

        return root_doc

    @staticmethod
    def _find_doc(root_doc: Doc, directory_path: str) -> Doc:
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory {directory_path} does not exist.")

        # self.doc is a recursive structure with a path and children: [doc1, doc2, ...]
        # if the path of the doc matches the directory_path return all the children
        def find_document(doc: Doc, directory_path: str) -> Optional[Doc]:
            if directory_path in [
                doc.path,
                f"{doc.path}/",
                f"/{doc.path}",
                f"/{doc.path}/",
                f"./{doc.path}",
                f"./{doc.path}/",
            ]:
                return doc

            # if the doc is a directory, search in its children
            for child in doc.children:
                if os.path.isdir(child.path):
                    target = find_document(child, directory_path)
                    if target:
                        return target

            return None

        if directory_path in [".", "./", "/"]:
            return root_doc
        doc = find_document(root_doc, directory_path)
        return doc

    def get_prompt(self, prompt_file_name) -> str:
        with open(f"supercoder/prompts/{prompt_file_name}", "r") as file:
            return file.read()
