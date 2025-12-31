"""
FastMCP Server Implementation

This implements the same tools as mcp_server but using the FastMCP library,
which handles the MCP protocol automatically.

Usage:
    # Run with SSE transport (HTTP):
    fastmcp run server:mcp --transport sse --port 8000

    # Run with stdio transport (for CLI tools like Claude Desktop):
    fastmcp run server:mcp

    # Or run directly (defaults to stdio):
    python server.py
"""
from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# Create the FastMCP server instance
mcp = FastMCP(
    name="Bedrock Chatbot Tools",
    instructions="A set of utility tools for the Bedrock chatbot."
)


@mcp.tool()
def get_current_time() -> dict[str, str]:
    """Get the current date and time in the server's timezone."""
    now = datetime.now()
    return {
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d")
    }


@mcp.tool()
def calculate(expression: str) -> dict[str, Any]:
    """
    Evaluate a mathematical expression and return the result.

    Args:
        expression: The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5', '2 ** 8').
                   Supports basic arithmetic operations (+, -, *, /, **, %).
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def list_files(directory: str = ".") -> dict[str, Any]:
    """
    List all files and directories in the specified directory path.

    Args:
        directory: The directory path to list files from. Defaults to current directory.
    """
    try:
        path = Path(directory)
        files = [f.name for f in path.iterdir()]
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Run with stdio transport (default for MCP)
    mcp.run()
