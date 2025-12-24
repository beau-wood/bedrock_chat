"""Simple tool implementations."""
from datetime import datetime
from pathlib import Path


def get_current_time():
    """Get the current date and time."""
    now = datetime.now()
    return {
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d")
    }


def calculate(expression: str):
    """Evaluate a math expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


def list_files(directory: str = "."):
    """List files in a directory."""
    try:
        path = Path(directory)
        files = [f.name for f in path.iterdir()]
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}