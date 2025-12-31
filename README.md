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

```bash
# run API server for MCP tools
python mcp_server/server.py
# test mcp - curl http://localhost:8000/tools

# Run the chatbot w/ mcp tools
python src/chatbot_with_tools.py
# Sample tool use:
# What files are in this directory?
# What time is it?

# OR
# Run the chatbot w/o tools
python src/chatbot.py
```

## Project Structure

```
bedrock-chatbot/
├── config/
│   ├── __init__.py
│   └── settings.py           # Configuration management
├── logs/                     # Log files directory
├── mcp_server/
│   ├── __init__.py
│   ├── server.py             # FastAPI MCP server
│   └── tools.py              # MCP tool definitions
├── src/
│   ├── __init__.py
│   ├── chatbot.py            # Sample chatbot code w/o mcp tools
│   └── chatbot_with_tools.py # Chatbot with MCP tools integration
├── .env                      # Environment variables (not in git)
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Environment Variables

- `AWS_REGION`: AWS region for Bedrock
- `BEDROCK_MODEL_ID`: Claude model identifier
- `MAX_TOKENS`: Maximum response length
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Notes
- When running locally, aws creds come from ~/.aws/credentials
- When deploying to cloud, assign an IAM role to the instance so that creds are automatically created/rotated (boto understands automatically)


## MCP Testing Notes
1) run the FastAPI server: `python mcp_server/server.py`
2) Test the FastMCP:
```commandline
# List tools
curl http://localhost:8000/tools

# Get time
curl -X POST http://localhost:8000/call -H "Content-Type: application/json" -d '{"tool": "get_current_time"}'

# Calculate
curl -X POST http://localhost:8000/call -H "Content-Type: application/json" -d '{"tool": "calculate", "params": {"expression": "2+2"}}'

# List files
curl -X POST http://localhost:8000/call -H "Content-Typ
```
