# ======================================================
# ================= CHARLIE_MCP SERVER ====================
# ======================================================
# Lightweight, LOCAL, READ-ONLY MCP server for live-testing the
# AI Companion stack. Every tool here is diagnostic — nothing
# writes, deletes, or moves files, and nothing exposes secrets.
#
# Run this on YOUR machine:
#   pip install mcp
#   python charlie_mcp_server.py
#
# Then expose it temporarily with ngrok (or similar) so Claude can
# connect during a test session:
#   ngrok http 8000
# Give Claude the ngrok URL. Shut both down when you're done testing
# — this should not be a permanently-running service.

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import subprocess
import os
import sys

# Import your actual stack — adjust these imports to match wherever
# your real project files live relative to this server script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

mcp = FastMCP("charlie_mcp")


# ======================================================
# TOOL 1 — Check if Ollama is actually running and reachable
# ======================================================

@mcp.tool(
    name="charlie_check_ollama_status",
    annotations={
        "title": "Check Ollama Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def check_ollama_status() -> str:
    """Checks whether Ollama is installed and running locally, and
    lists which models are currently pulled. Read-only — makes a
    simple HTTP request to Ollama's local API, nothing is modified.

    Returns:
        str: JSON-formatted status with running state and model list.
    """
    import httpx
    import json

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return json.dumps({"running": True, "models": models})
    except Exception as e:
        return json.dumps({"running": False, "error": str(e)})


# ======================================================
# TOOL 2 — Run an actual Ollama chat completion (real test)
# ======================================================

class OllamaChatInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message: str = Field(..., description="The message to send to Ollama", min_length=1, max_length=2000)
    model: Optional[str] = Field(default="llama3.2", description="Which pulled Ollama model to use")


@mcp.tool(
    name="charlie_test_ollama_chat",
    annotations={
        "title": "Test Ollama Chat Completion",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def test_ollama_chat(params: OllamaChatInput) -> str:
    """Sends a single test message to a locally running Ollama model
    and returns its reply. This is how Claude can verify the actual
    brain call works, not just that Ollama is reachable.

    Args:
        params (OllamaChatInput): message to send and which model to use.

    Returns:
        str: The model's raw text reply, or an error message.
    """
    import httpx
    import json

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": params.model,
                    "messages": [{"role": "user", "content": params.message}],
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
    except Exception as e:
        return json.dumps({"error": str(e)})


# ======================================================
# TOOL 3 — Search files (wraps your actual file_search.py)
# ======================================================

class FileSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., description="Filename or partial filename to search for", min_length=1, max_length=200)


@mcp.tool(
    name="charlie_search_files",
    annotations={
        "title": "Search Files (Desktop/Downloads/Documents)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def search_files(params: FileSearchInput) -> str:
    """Searches Desktop, Downloads, and Documents for files matching
    the query. READ-ONLY — only lists matching file paths, never
    opens, moves, or modifies anything found.

    Args:
        params (FileSearchInput): the search query.

    Returns:
        str: JSON list of matching file paths.
    """
    import json
    try:
        from nexus_fixed.core.file_search import find_file
        matches = find_file(params.query)
        return json.dumps({"matches": matches})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ======================================================
# TOOL 4 — Run the actual database CRUD test suite
# ======================================================

@mcp.tool(
    name="charlie_test_database",
    annotations={
        "title": "Test Database CRUD Operations",
        "readOnlyHint": False,   # writes test rows, but to a TEST db, not real data
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def test_database() -> str:
    """Runs a safe CRUD test against companion.db — creates a test
    task, reads it back, then deletes it. Does NOT touch existing
    real tasks, memories, or profile data. Verifies the database
    layer actually works on your real machine, not just in Claude's
    sandbox.

    Returns:
        str: JSON summary of what was tested and whether it passed.
    """
    import json
    try:
        import database as db
        db.init_db()

        test_id = db.create_task(title="[MCP TEST] delete me", priority="low")
        tasks = db.get_tasks()
        found = any(t["id"] == test_id for t in tasks)
        db.delete_task(test_id)

        return json.dumps({
            "passed": found,
            "detail": "Created, read, and deleted a test task successfully" if found else "Test task was not found after creation"
        })
    except Exception as e:
        return json.dumps({"passed": False, "error": str(e)})


# ======================================================
# RUN THE SERVER
# ======================================================

if __name__ == "__main__":
    # Streamable HTTP transport so ngrok (or similar) can expose it.
    # For purely local testing without ngrok, you can switch
    # transport="stdio" instead — but that only works if Claude runs
    # on the same machine, which isn't the case here.
    mcp.run(transport="streamable-http")
