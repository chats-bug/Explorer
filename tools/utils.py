import json
from pydantic import BaseModel, Field
from typing import List


def tool_schema(f: BaseModel):
    schema = f.model_json_schema(mode='serialization')
    schema.pop("type")
    schema.pop("title")
    for s in schema["properties"].keys():
        if "title" in schema["properties"][s].keys():
            schema["properties"][s].pop("title")
    # rename "properties" to "args"
    schema["arguments"] = schema.pop("properties")
    schema["required"] = schema.pop("required")
    return json.dumps(schema, indent=2)


def generate_tools_subprompt(tools):
    tool_descriptions = []
    for tool in tools.keys():
        f = tools[tool]
        f_doc = f.__doc__ or ""
        tool_descriptions = tool_descriptions + [f'"{tool}": {f_doc.strip()}\nargs json schema:\n{tool_schema(f)}\n']
    return numbered_list(tool_descriptions)


def numbered_list(strings: List[str] = Field(..., description="List of strings to concatenate into a numbered list")):
    i = 1
    r = ""
    for s in strings:
        r = r + f"{i}. {s}\n"
        i = i + 1
    return r


if __name__ == "__main__":
    from tools import ReadCodeSnippet, ReadCode, ListFiles, SemanticCodeSearch
    print(generate_tools_subprompt({
        "read_snippet": ReadCodeSnippet,
        "read_code": ReadCode,
        "list_files": ListFiles,
        "semantic_code_search": SemanticCodeSearch,
    }))
