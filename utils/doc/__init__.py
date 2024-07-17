import json
import os
from .doc_model import Doc, find_doc
from .doc_generation import DocUtils


def get_doc(repo_path: str) -> Doc:
    doc_index_path = f"saved_states/indices/{repo_path}/default.json"
    if not os.path.exists(doc_index_path):
        doc_utils = DocUtils(
            path=repo_path,
            gitignore_path=f"{repo_path}/.gitignore",
        )
        doc_utils.generate_documentation(doc_utils.root_doc)
        root_doc = doc_utils.root_doc
        if not os.path.exists(f"saved_states/indices/{repo_path}"):
            os.makedirs(f"saved_states/indices/{repo_path}")
        with open(doc_index_path, "w") as f:
            f.write(json.dumps(root_doc.get_dict(), indent=4))
    else:
        root_doc = Doc(**json.loads(open(doc_index_path).read()))
    return root_doc
