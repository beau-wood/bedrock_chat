import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the chatbot."""
    
    # AWS Settings
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
    
    # Bedrock Settings
    BEDROCK_MODEL_ID = os.getenv(
        'BEDROCK_MODEL_ID', 
        'anthropic.claude-3-5-sonnet-20241022-v2:0'
    )
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '4096'))
    
    # Deployment Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required = ['AWS_REGION', 'BEDROCK_MODEL_ID']
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
