#!/usr/bin/env python3
"""A small, read-only Gemini agent for exploring the current folder.

Run:
  python3 agent_gemini.py "How does this project work?"
"""

import os
import sys
from pathlib import Path

from google import genai
from google.genai import types


# 1. Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY before running this program.")

# Change GEMINI_MODEL if this model is unavailable for your API key.
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
client = genai.Client(api_key=API_KEY)

# The agent is only allowed to read files inside the folder where it runs.
ROOT = Path.cwd().resolve()


# 2. Local tools
# ---------------------------------------------------------------------------
# Gemini can ASK to call these functions. Python runs them. This is the
# important safety boundary: the model never gets direct computer access.

def safe_path(file_name: str) -> Path:
    """Make sure a requested path stays inside the project folder."""
    path = (ROOT / file_name).resolve()
    if path != ROOT and ROOT not in path.parents:
        raise ValueError("That path is outside this project.")
    return path


def list_files(folder: str = ".") -> str:
    """Return the files and folders in one folder."""
    try:
        return "\n".join(
            f"{item.name}/" if item.is_dir() else item.name
            for item in safe_path(folder).iterdir()
        )
    except Exception as error:
        return f"Error: {error}"


def read_file(file_name: str) -> str:
    """Read a text file. Keep it short enough to send to the model."""
    try:
        text = safe_path(file_name).read_text(encoding="utf-8")
        return text[:8000] + ("\n...[truncated]" if len(text) > 8000 else "")
    except Exception as error:
        return f"Error: {error}"


def search_code(query: str) -> str:
    """Find up to 10 matching lines in common source files."""
    try:
        matches = []
        source_extensions = {".py", ".js", ".mjs", ".ts", ".json", ".md"}
        ignored_folders = {".git", ".venv", "node_modules", "dist", "build"}

        for file_path in ROOT.rglob("*"):
            if len(matches) == 10:
                break
            if not file_path.is_file() or file_path.suffix not in source_extensions:
                continue
            if any(folder in ignored_folders for folder in file_path.parts):
                continue

            for number, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
                if query.lower() in line.lower():
                    matches.append(f"{file_path.relative_to(ROOT)}:{number}: {line.strip()}")
                    if len(matches) == 10:
                        break

        return "\n".join(matches) or "No matches found."
    except Exception as error:
        return f"Error: {error}"


def run_tool(name: str, arguments: dict) -> str:
    """Map Gemini's requested tool name to a normal Python function."""
    if name == "list_files":
        return list_files(arguments.get("folder", "."))
    if name == "read_file":
        return read_file(arguments.get("file_name", ""))
    if name == "search_code":
        return search_code(arguments.get("query", ""))
    return f"Error: Unknown tool: {name}"


# 3. Tool descriptions sent to Gemini
# ---------------------------------------------------------------------------

tools = [types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="list_files",
        description="List files and folders. Use this first to explore a project.",
        parameters_json_schema={
            "type": "object",
            "properties": {"folder": {"type": "string"}},
        },
    ),
    types.FunctionDeclaration(
        name="read_file",
        description="Read one text file after finding it with list_files.",
        parameters_json_schema={
            "type": "object",
            "properties": {"file_name": {"type": "string"}},
            "required": ["file_name"],
        },
    ),
    types.FunctionDeclaration(
        name="search_code",
        description="Search source files for a specific word or identifier.",
        parameters_json_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ),
])]

INSTRUCTIONS = """
You answer questions about this codebase. First list the root folder, then read
relevant files before answering. Cite file names in the final answer. Never say
you read a file when a tool returned an Error.
"""


# 4. The agent loop
# ---------------------------------------------------------------------------

def ask_agent(question: str) -> None:
    """Ask Gemini a question and handle its tool calls."""
    history = [types.Content(
        role="user",
        parts=[types.Part.from_text(text=question)],
    )]

    # Five steps stops an accidental endless loop.
    for _step in range(5):
        response = client.models.generate_content(
            model=MODEL,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCTIONS,
                tools=tools,
            ),
        )

        calls = response.function_calls or []

        # No requested function means Gemini has written its final answer.
        if not calls:
            print("\nFINAL ANSWER:\n" + (response.text or "No answer returned."))
            return

        # Do not rebuild this message. Gemini adds metadata here that it needs
        # to continue reasoning correctly after a tool result.
        history.append(response.candidates[0].content)

        results = []
        for call in calls:
            arguments = dict(call.args or {})
            print(f"Tool call: {call.name}({arguments})")
            result = run_tool(call.name, arguments)
            results.append(types.Part.from_function_response(
                name=call.name,
                response={"result": result},
            ))

        # Send tool results back as a user message for GenerateContent.
        history.append(types.Content(role="user", parts=results))

    print("\nThe agent reached its five-tool-call limit. Try a more specific question.")


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "How does this project work?"
    ask_agent(question)
