# AWS Bedrock Claude Chatbot + MCP

Learning to integrate AWS Bedrock + FastAPI + FastMCP

## Setup

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Configure AWS credentials:
   ```bash
   aws configure
   ```

## Usage

### Option 1: FastAPI Server (mcp_server/)
Custom MCP implementation using FastAPI with MCP-like JSON format.  Uses http for communication.
Use `src/chatbot_with_tools.py` when using `mcp_server/server.py`

```commandline
┌─────────────┐                    ┌──────────────┐
│   Chatbot   │                    │ FastAPI      │
│             │                    │ MCP Server   │
│             │                    │ :8000        │
│             │─────HTTP POST─────>│              │
│             │   /tools /call     | def call_    │
│             │   {tool, params}   │   tool()     │
│             │<────HTTP 200───────│              │
│             │   JSON response    │              │
└─────────────┘                    └──────────────┘
     ↑                                    ↑
     │                                    │
  Started                              Started
  manually                             manually
  (Terminal 2)                         (Terminal 1)
```

```bash
# Run the server
python mcp_server/server.py

# Test endpoints
curl http://localhost:8000/tools
curl -X POST http://localhost:8000/call -H "Content-Type: application/json" -d '{"tool": "get_current_time"}'
curl -X POST http://localhost:8000/call -H "Content-Type: application/json" -d '{"tool": "calculate", "params": {"expression": "2+2"}}'

# Run the chatbot
python src/chatbot_with_tools.py
```

### Option 2: FastMCP Server (fastmcp_server/)
FastMCP implementation using stdio for communication.  Use `src/chatbot_with_fastmcp.py` - this runs standalone without needing to run separate MCP server
```
┌─────────────┐                    ┌──────────────┐
│   Chatbot   │                    │ FastMCP      │
│             │                    │ Server       │
│             │─────stdin─────────>│              │
│             │   JSON-RPC         │ @mcp.tool()  │
│             │<────stdout─────────│ functions    │
│             │   responses        │              │
└─────────────┘                    └──────────────┘
```

```bash
# The chatbot_with_fastmcp code does the following:
# 1. Start `fastmcp_server/server.py` as a subprocess
# 2. Connect via stdin/stdout
# 3. Initialize the MCP connection
# 4. Load available tools
# 5. Use tools when Claude needs them

python src/chatbot_with_fastmcp.py
```


## Project Structure

```
bedrock-chatbot/
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration management
├── fastmcp_server/
│   ├── __init__.py
│   └── server.py                # FastMCP server
├── mcp_server/
│   ├── __init__.py
│   ├── server.py                # FastAPI server (custom MCP-like API)
│   └── tools.py                 # Tool definitions with registry
├── src/
│   ├── __init__.py
│   ├── chatbot.py               # Sample chatbot code w/o mcp tools
│   └── chatbot_with_fastmcp.py  # Chatbot with FastMCP integration (standalone bot that runs the fastmcp subprocess)
│   └── chatbot_with_tools.py    # Chatbot with MCP tools integration (requires running mcp server separately)
├── logs/                        # Log files directory
├── .env                         # Environment variables (not in git)
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Environment Variables

- `AWS_REGION`: AWS region for Bedrock
- `BEDROCK_MODEL_ID`: Claude model identifier
- `MAX_TOKENS`: Maximum response length
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Notes
- When running locally, aws creds come from ~/.aws/credentials
- When deploying to cloud, assign an IAM role to the instance so that creds are automatically created/rotated (boto understands automatically)


## Todos
- What is better, FastMCP w/ stdio or wrapped in FastAPI?
- At LK we wrap everything in FastAPI right?