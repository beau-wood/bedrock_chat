"""MCP tool implementations with metadata."""
from datetime import datetime
from pathlib import Path
from typing import Callable, Any

# Registry to hold all tools with their metadata
TOOL_REGISTRY: dict[str, dict[str, Any]] = {}


def register_tool(
    name: str,
    description: str,
    input_schema: dict[str, Any] | None = None
) -> Callable:
    """Decorator to register a tool with MCP metadata."""
    def decorator(func: Callable) -> Callable:
        TOOL_REGISTRY[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema or {
                "type": "object",
                "properties": {},
                "required": []
            },
            "function": func
        }
        return func
    return decorator


def get_tools_list() -> list[dict[str, Any]]:
    """Return all tools in MCP format (without the function reference)."""
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["input_schema"]
        }
        for tool in TOOL_REGISTRY.values()
    ]


def call_tool(name: str, params: dict[str, Any]) -> dict[str, Any]:
    """Call a tool by name with the given parameters."""
    if name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {name}"}

    tool = TOOL_REGISTRY[name]
    try:
        return tool["function"](**params)
    except TypeError as e:
        return {"error": f"Invalid parameters: {e}"}


# Tool implementations

@register_tool(
    name="get_current_time",
    description="Get the current date and time in the server's timezone.",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_current_time() -> dict[str, str]:
    """Get the current date and time."""
    now = datetime.now()
    return {
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d")
    }


@register_tool(
    name="calculate",
    description="Evaluate a mathematical expression and return the result. Supports basic arithmetic operations (+, -, *, /, **, %).",
    input_schema={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5', '2 ** 8')"
            }
        },
        "required": ["expression"]
    }
)
def calculate(expression: str) -> dict[str, Any]:
    """Evaluate a math expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="list_files",
    description="List all files and directories in the specified directory path.",
    input_schema={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "The directory path to list files from. Defaults to current directory.",
                "default": "."
            }
        },
        "required": []
    }
)
def list_files(directory: str = ".") -> dict[str, Any]:
    """List files in a directory."""
    try:
        path = Path(directory)
        files = [f.name for f in path.iterdir()]
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}
