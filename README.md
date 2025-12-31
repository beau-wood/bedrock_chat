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
python src/chatbot.py
```

## Project Structure

```
bedrock-chatbot/
├── venv/                 # Virtual environment
├── src/
│   └── chatbot.py       # Main chatbot code
├── config/
│   └── settings.py      # Configuration management
├── .env                 # Environment variables (not in git)
├── .env.example         # Example environment variables
├── .gitignore          # Git ignore rules
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Deployment

This structure is ready for deployment to:
- AWS Lambda
- AWS ECS/Fargate
- AWS EC2
- Docker containers
- Any cloud platform

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
