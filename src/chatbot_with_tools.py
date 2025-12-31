# File: src/chatbot_with_tools.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
import json
import logging
import os
import requests
from typing import List, Dict
from config.settings import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaudeChatbotWithTools:
    """AWS Bedrock Claude chatbot with MCP tool integration."""

    def __init__(self, model_id: str = None, region: str = None, mcp_url: str = "http://localhost:8000"):
        """
        Initialize the chatbot with AWS Bedrock client and MCP server.

        Args:
            model_id: The Claude model to use
            region: AWS region
            mcp_url: URL of the MCP server
        """
        self.model_id = model_id or Config.BEDROCK_MODEL_ID
        self.region = region or Config.AWS_REGION
        self.mcp_url = mcp_url

        # Initialize Bedrock client
        try:
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

            if access_key and secret_key:
                session = boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=self.region
                )
                self.bedrock = session.client(service_name='bedrock-runtime')
            else:
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

        # Load available tools from MCP server
        self.tools = self._load_tools()

    def _load_tools(self) -> List[Dict]:
        """Load available tools from MCP server."""
        try:
            response = requests.get(f"{self.mcp_url}/tools", timeout=5)
            if response.status_code == 200:
                tools = response.json()
                logger.info(f"Loaded {len(tools)} tools from MCP server")
                return tools
            else:
                logger.warning("MCP server not available, running without tools")
                return []
        except Exception as e:
            logger.warning(f"Could not connect to MCP server: {e}")
            return []

    def _call_mcp_tool(self, tool_name: str, params: Dict) -> Dict:
        """Call a tool on the MCP server."""
        try:
            response = requests.post(
                f"{self.mcp_url}/call",
                json={"tool": tool_name, "params": params},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"MCP server returned status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def send_message(self, user_message: str) -> str:
        """
        Send a message to Claude and handle tool calls.

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

        # Prepare the request body with tools
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "messages": self.conversation_history
        }

        # Add tools if available
        if self.tools:
            request_body["tools"] = self.tools

        try:
            # Call Bedrock API
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            response_body = json.loads(response['body'].read())

            # Check if Claude wants to use tools
            if response_body.get('stop_reason') == 'tool_use':
                return self._handle_tool_use(response_body)
            else:
                # Regular text response
                assistant_message = response_body['content'][0]['text']

                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })

                return assistant_message

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _handle_tool_use(self, response_body: Dict) -> str:
        """Handle tool use requests from Claude."""
        content_blocks = response_body['content']

        # Add Claude's response to history (including tool use)
        self.conversation_history.append({
            "role": "assistant",
            "content": content_blocks
        })

        # Execute each tool call
        tool_results = []
        text_response = ""

        for block in content_blocks:
            if block['type'] == 'text':
                text_response = block['text']

            elif block['type'] == 'tool_use':
                tool_name = block['name']
                tool_input = block['input']
                tool_use_id = block['id']

                logger.info(f"Claude wants to use tool: {tool_name} with input: {tool_input}")

                # Call the MCP tool
                result = self._call_mcp_tool(tool_name, tool_input)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result)
                })

        # Send tool results back to Claude
        self.conversation_history.append({
            "role": "user",
            "content": tool_results
        })

        # Get Claude's final response
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "messages": self.conversation_history,
            "tools": self.tools
        }

        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            response_body = json.loads(response['body'].read())
            final_message = response_body['content'][0]['text']

            self.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })

            return final_message

        except Exception as e:
            return f"Error processing tool results: {str(e)}"

    def reset_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")


def main():
    """Main function to run the chatbot with tools."""
    print("Claude Chatbot with MCP Tools")
    print("=" * 50)
    print("Type 'quit' to exit or 'reset' to clear history")
    print(f"Using model: {Config.BEDROCK_MODEL_ID}")
    print("MCP Tools enabled: get_current_time, calculate, list_files\n")

    # Initialize chatbot
    try:
        chatbot = ClaudeChatbotWithTools()
    except Exception as e:
        print(f"Failed to initialize chatbot: {e}")
        return

    while True:
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

        print("\nClaude: ", end="")
        response = chatbot.send_message(user_input)
        print(response)
        print()


if __name__ == "__main__":
    main()