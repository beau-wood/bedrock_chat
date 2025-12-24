import boto3
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Dict
from config.settings import Config

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Configure logging with both file and console handlers
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_level = getattr(logging, Config.LOG_LEVEL)

# Create handlers
file_handler = RotatingFileHandler(
    log_dir / 'chatbot.log',
    maxBytes=10*1024*1024,  # 10MB per file
    backupCount=5            # Keep 5 old files
)
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter(log_format))

console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(log_format))

# Configure root logger
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)


class ClaudeChatbot:
    """AWS Bedrock Claude chatbot with production-ready features."""
    
    def __init__(self, model_id: str = None, region: str = None):
        """
        Initialize the chatbot with AWS Bedrock client.
        
        Args:
            model_id: The Claude model to use (defaults to config)
            region: AWS region (defaults to config)
        """
        self.model_id = model_id or Config.BEDROCK_MODEL_ID
        self.region = region or Config.AWS_REGION
        
        try:
            self.bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region
            )
            logger.info(f"Initialized Bedrock client in region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
        
        self.conversation_history: List[Dict] = []
        self.max_tokens = Config.MAX_TOKENS
    
    def send_message(self, user_message: str) -> str:
        """
        Send a message to Claude and get a response.
        
        Args:
            user_message: The user's input message
            
        Returns:
            Claude's response as a string
        """
        if not user_message.strip():
            return "Please provide a message."
        
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare the request body
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "messages": self.conversation_history
        }
        
        try:
            logger.info(f"Sending request to model: {self.model_id}")
            logger.info(f"Request body: {json.dumps(request_body)}")
            
            # Call Bedrock API
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            assistant_message = response_body['content'][0]['text']
            
            # Add assistant response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            logger.info("Successfully received response from Claude")
            return assistant_message
            
        except self.bedrock.exceptions.ValidationException as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except self.bedrock.exceptions.ThrottlingException as e:
            error_msg = "Rate limit exceeded. Please try again in a moment."
            logger.warning(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def reset_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_conversation_length(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.conversation_history)


def main():
    """Main function to run the chatbot."""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    print("Claude Chatbot (AWS Bedrock)")
    print("=" * 50)
    print("Type 'quit' to exit or 'reset' to clear history")
    print(f"Using model: {Config.BEDROCK_MODEL_ID}\n")
    
    # Initialize chatbot
    try:
        chatbot = ClaudeChatbot()
    except Exception as e:
        print(f"Failed to initialize chatbot: {e}")
        return
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
            
        if user_input.lower() == 'reset':
            chatbot.reset_conversation()
            print("Conversation reset.\n")
            continue
        
        # Get and display response
        print("\nClaude: ", end="")
        response = chatbot.send_message(user_input)
        print(response)
        print()


if __name__ == "__main__":
    main()
