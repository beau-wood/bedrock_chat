# AWS Bedrock Claude Chatbot

A production-ready Python chatbot using AWS Bedrock and Claude.

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
- 
