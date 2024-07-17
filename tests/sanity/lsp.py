import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from tools import LSPUtils, LSPRequestTypes, LSPSupportedLanguages
from config import console


def main():
    lsp_tool = LSPUtils(
        language=LSPSupportedLanguages.PYTHON,
        repo_path=os.path.abspath("workspace/SuperAGI"),
        file_path=os.path.abspath("workspace/SuperAGI/superagi/tools/code/__init__.py"),
        line_number=1,
        symbol="coding_toolkit",
        request_type=LSPRequestTypes.DEFINITION,
    )
    resp = lsp_tool.run()
    console.print(resp["response"])


if __name__ == "__main__":
    main()
