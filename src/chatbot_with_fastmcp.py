# File: src/chatbot_with_fastmcp.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
import json
import logging
import os
import subprocess
from typing import List, Dict, Optional
from config.settings import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FastMCPClient:
    """Simple client to communicate with FastMCP server via stdio."""

    def __init__(self, server_script: str):
        """
        Initialize FastMCP client by starting the server process.

        Args:
            server_script: Path to the FastMCP server script
        """
        self.process = subprocess.Popen(
            [sys.executable, server_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.request_id = 0
        logger.info(f"Started FastMCP server: {server_script}")

        # Initialize the MCP connection
        self._initialize()

    def _initialize(self):
        """Perform MCP initialization handshake."""
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "chatbot-client", "version": "1.0"}
            }
        }
        response = self._send_request(init_request)

        # Send initialized notification
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        self.process.stdin.write(json.dumps(init_notif) + "\n")
        self.process.stdin.flush()

        logger.info("FastMCP connection initialized")

    def _next_id(self):
        """Generate next request ID."""
        self.request_id += 1
        return self.request_id

    def _send_request(self, request: dict) -> dict:
        """Send a JSON-RPC request and get response."""
        # Send request
        request_json = json.dumps(request) + '\n'
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            return {"error": "No response from server"}

        try:
            response = json.loads(response_line)
            return response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {response_line}")
            return {"error": str(e)}

    def list_tools(self) -> List[dict]:
        """Get list of available tools."""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {}
        }
        response = self._send_request(request)

        # FastMCP returns tools in result.tools
        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]

            # Convert FastMCP tool format to Claude format
            claude_tools = []
            for tool in tools:
                claude_tools.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["inputSchema"]
                })
            return claude_tools
        return []

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool with given arguments."""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        response = self._send_request(request)

        # FastMCP returns result in result.content[0].text
        if "result" in response:
            result = response["result"]
            if "content" in result and len(result["content"]) > 0:
                # Parse the text content (FastMCP returns stringified dict)
                text = result["content"][0].get("text", "{}")
                try:
                    return eval(text)  # Convert string dict back to dict
                except:
                    return {"result": text}

        return {"error": "Failed to get result"}

    def close(self):
        """Close the FastMCP server process."""
        if self.process:
            self.process.stdin.close()
            self.process.terminate()
            self.process.wait()
            logger.info("Closed FastMCP server")


class ClaudeChatbotWithFastMCP:
    """AWS Bedrock Claude chatbot with FastMCP tool integration."""

    def __init__(self, model_id: str = None, region: str = None, mcp_server_script: str = None):
        """
        Initialize the chatbot with AWS Bedrock client and FastMCP server.

        Args:
            model_id: The Claude model to use
            region: AWS region
            mcp_server_script: Path to FastMCP server script
        """
        self.model_id = model_id or Config.BEDROCK_MODEL_ID
        self.region = region or Config.AWS_REGION

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

        # Initialize FastMCP client
        if mcp_server_script:
            try:
                self.mcp_client = FastMCPClient(mcp_server_script)
                self.tools = self._load_tools()
            except Exception as e:
                logger.warning(f"Failed to start FastMCP server: {e}")
                self.mcp_client = None
                self.tools = []
        else:
            self.mcp_client = None
            self.tools = []

    def _load_tools(self) -> List[Dict]:
        """Load available tools from FastMCP server."""
        if not self.mcp_client:
            return []

        try:
            tools = self.mcp_client.list_tools()
            logger.info(f"Loaded {len(tools)} tools from FastMCP server")
            return tools
        except Exception as e:
            logger.warning(f"Could not load tools from FastMCP server: {e}")
            return []

    def _call_mcp_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a tool via FastMCP."""
        if not self.mcp_client:
            return {"error": "FastMCP client not available"}

        try:
            result = self.mcp_client.call_tool(tool_name, arguments)
            return result
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

        for block in content_blocks:
            if block['type'] == 'tool_use':
                tool_name = block['name']
                tool_input = block['input']
                tool_use_id = block['id']

                logger.info(f"Claude wants to use tool: {tool_name} with input: {tool_input}")

                # Call the FastMCP tool
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

    def close(self):
        """Close the FastMCP client."""
        if self.mcp_client:
            self.mcp_client.close()


def main():
    """Main function to run the chatbot with FastMCP tools."""
    print("Claude Chatbot with FastMCP Tools")
    print("=" * 50)
    print("Type 'quit' to exit or 'reset' to clear history")
    print(f"Using model: {Config.BEDROCK_MODEL_ID}\n")

    # Initialize chatbot with FastMCP server
    fastmcp_script = "fastmcp_server/server.py"

    try:
        chatbot = ClaudeChatbotWithFastMCP(mcp_server_script=fastmcp_script)
        print(f"FastMCP tools loaded: {len(chatbot.tools)}\n")
    except Exception as e:
        print(f"Failed to initialize chatbot: {e}")
        return

    try:
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

    finally:
        # Clean up
        chatbot.close()


if __name__ == "__main__":
    main()