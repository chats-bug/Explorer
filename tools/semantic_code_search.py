# import json
# import os
# from typing import Optional

# from lancedb.table import Table
# from pydantic import Field

# from lib import logger
# from tools import BaseTool
# from utils.code_search import Indexer


# class SemanticCodeSearch(BaseTool):
#     """This tool searches relevant code snippets in files. It accepts a query and returns the relevant code snippets \
#     along with file paths. Only supports python files for now. But looking in the same directory for other files might \
#     also help, if you need to edit files in other languages as well. \
#     REMEMBER: This tool can only search in functions and classes. If there is some code outside of functions or classes, \
#     it will not be searched. So make sure to also search for the code in the file if it is not found in the results.
#     """

#     index: Indexer = Field(
#         ..., description="The indexer to search the file in.", exclude=True
#     )
#     table: Table = Field(
#         ..., description="The table to search the file in.", exclude=True
#     )
#     query: str = Field(
#         ...,
#         description="The query you want to search. Given this objective, the tool will return "
#         "relevant code snippets from the repo.",
#     )
#     file_path: Optional[str] = Field(
#         None,
#         description="The path to the file you want to search in. If not provided, "
#         "the tool will search in all files.",
#         alias="file_to_search",
#     )
#     dir_path: Optional[str] = Field(
#         None,
#         description="The path to the directory you want to search in. If not provided, "
#         "the tool will search in the root directory.",
#         alias="dir_to_search",
#     )

#     def run(self, *args, **kwargs):
#         try:
#             results = self.index.get_filtered_results(
#                 table=self.table,
#                 query=self.query,
#                 file_path=self.file_path,
#                 dir_path=self.dir_path,
#             )

#             return {"success": True, "response": json.dumps(results, indent=4)}
#         except Exception as e:
#             logger.critical(e)
#             return {"success": False, "response": e.__str__()}

#     class Config:
#         arbitrary_types_allowed = True
