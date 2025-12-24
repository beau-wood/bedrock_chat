"""Simple FastAPI server."""
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from tools import get_current_time, calculate, list_files

app = FastAPI()


class ToolRequest(BaseModel):
    tool: str
    params: dict = {}


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/tools")
def list_tools():
    return {
        "tools": ["get_current_time", "calculate", "list_files"]
    }


@app.post("/call")
def call_tool(request: ToolRequest):
    if request.tool == "get_current_time":
        return get_current_time()

    elif request.tool == "calculate":
        return calculate(request.params.get("expression", ""))

    elif request.tool == "list_files":
        return list_files(request.params.get("directory", "."))

    else:
        return {"error": "Unknown tool"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)