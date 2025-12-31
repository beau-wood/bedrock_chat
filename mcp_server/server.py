from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from tools import get_tools_list, call_tool

app = FastAPI()


class ToolRequest(BaseModel):
    tool: str
    params: dict = {}


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/tools")
def list_tools():
    """Return all available tools in MCP format."""
    return get_tools_list()


@app.post("/call")
def call_tool_endpoint(request: ToolRequest):
    """Call a tool by name with the given parameters."""
    return call_tool(request.tool, request.params)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
