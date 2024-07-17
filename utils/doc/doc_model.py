import os
from typing import Optional, List, Dict, Any
import concurrent.futures

from pydantic import BaseModel

from lib import logger


class Doc(BaseModel):
    children: Optional[List["Doc"]]
    path: str
    documentation: str
    summary: str

    @classmethod
    def is_leaf_node(cls, doc: "Doc") -> bool:
        return doc.children is None or len(doc.children) == 0

    def get_documentation_from_children(self) -> list:
        return [child.documentation for child in self.children]

    def get_dict(self, depth=0, max_depth=10) -> Dict[str, Any]:
        if depth > max_depth:
            return {
                "path": self.path,
                "documentation": self.documentation,
                "summary": self.summary,
            }
        else:
            return {
                "path": self.path,
                "documentation": self.documentation,
                "summary": self.summary,
                "children": [
                    child.get_dict(depth + 1, max_depth) for child in self.children
                ],
            }


def list_files_in_doc(root_doc, directory_path: str) -> List[Doc]:
    if not os.path.isdir(directory_path):
        raise ValueError(f"Directory {directory_path} does not exist.")

    # self.doc is a recursive structure with a path and children: [doc1, doc2, ...]
    # if the path of the doc matches the directory_path return all the children
    def list_files(doc: Doc, dir_path: str) -> List[Doc]:
        logger.debug(f"Doc path: {doc.path}, Directory path: {dir_path}")
        if dir_path in [
            doc.path,
            f"{doc.path}/",
            f"/{doc.path}",
            f"/{doc.path}/",
            f"./{doc.path}",
            f"./{doc.path}/",
        ]:
            return doc.children

        # if the doc is a directory, search in its children
        for child in doc.children:
            if os.path.isdir(child.path):
                if files := list_files(child, dir_path):
                    return files

        return []

    if directory_path in [".", "./", "/"]:
        return root_doc.children
    files = list_files(root_doc, directory_path)
    return files


def find_doc(root_doc, directory_path: str) -> Optional[Doc]:
    if not os.path.isdir(directory_path):
        raise ValueError(f"Directory {directory_path} does not exist.")

    # self.doc is a recursive structure with a path and children: [doc1, doc2, ...]
    # if the path of the doc matches the directory_path return all the children
    def find_document(doc: Doc, dir_path: str) -> Optional[Doc]:
        if dir_path in [
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
                target = find_document(child, dir_path)
                if target:
                    return target

        return None

    if directory_path in [".", "./", "/"]:
        return root_doc
    target_doc = find_document(root_doc, directory_path)
    return target_doc


def fetch_docs(root_doc, files_dirs_path: List[str]) -> Dict[str, Doc]:
    if not files_dirs_path:
        return {}

    # Fetch the docs for the files
    # order the files by their depth
    # defined as the number of directories in the path
    # can be determined by splitting the path by '/'
    # reverse sort the files by their depth; lowest depth files first
    # files_dirs_path = sorted(files_dirs_path, key=lambda x: -len(x.split("/")))

    docs = {}
    target_doc = root_doc
    for file_or_dir in files_dirs_path:
        try:
            target = find_doc(target_doc, file_or_dir)
            if not target:
                logger.error(f"Doc not found for file/dir: {file_or_dir}")
            docs[file_or_dir] = target
        except ValueError:
            logger.error(f"Doc not found for file/dir: {file_or_dir}")
            # raise ValueError(f"Doc not found for file/dir: {file_or_dir}")
    return docs


def list_files_and_folders(filepath):
    files = []
    folders = []
    for element in os.listdir(filepath):
        element_starts_with_dot = element.startswith(".")
        element_in_gitignore = self.matches(os.path.join(filepath, element))
        element_ends_with_ignore_file_types = element.endswith(
            tuple(self.ignore_file_types)
        )

        if (
            element_starts_with_dot
            or element_in_gitignore
            or element_ends_with_ignore_file_types
        ):
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


def read_file(self, file_name):
    try:
        with open(file_name, "r") as file:
            return file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {file_name}")
        return ""


def _generate_documentation_for_file(file_content, filename):
    return ""


def _extract_documentation(response):
    return ""


def _extract_summary(response):
    return ""


def _generate_documentation_for_folder(folder_path, children_documentation):
    return ""


def generate_documentation(parent_node):
    files, folders = list_files_and_folders(parent_node.path)

    # generate the documentation for the files in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(
                _generate_documentation_for_file, read_file(file), file
            ): file
            for file in files
        }
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                response, filename = future.result()
                documentation = _extract_documentation(response)
                summary = _extract_summary(response)
                parent_node.children.append(
                    Doc(
                        path=filename,
                        children=[],
                        documentation=documentation,
                        summary=summary,
                    )
                )
            except Exception as exc:
                logger.error(f"Failed to generate documentation for file: {file}")

    for folder in folders:
        doc_for_folder = Doc(path=folder, children=[], documentation="", summary="")
        parent_node.children.append(doc_for_folder)
        generate_documentation(doc_for_folder)

    response, folder_name = _generate_documentation_for_folder(
        parent_node.path, parent_node.get_documentation_from_children()
    )
    parent_node.documentation = _extract_documentation(response)
    parent_node.summary = _extract_summary(response)
