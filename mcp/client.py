"""
MCP Client — connects to external MCP servers over HTTP/SSE.

This is for when you want to connect to a REAL external MCP server
(like a hosted Brave Search MCP, or a third-party data provider).

For internal Django tools, we call tool functions directly (see mcp/tools.py).
This client is for the external server case.

Usage example:
    client = MCPHTTPClient("https://mcp.brave.com/sse", api_key="...")
    result = client.call_tool("brave_search", {"query": "AI trends 2025"})
"""
import json
import logging
import httpx
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPHTTPClient:
    """
    Client for external MCP servers using HTTP/SSE transport.
    Follows the MCP protocol: initialize → list tools → call tool.
    """

    def __init__(self, server_url: str, api_key: Optional[str] = None, timeout: int = 15):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._session_id = None
        self._available_tools = None

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def initialize(self) -> bool:
        """Initialize MCP session."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.server_url}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "clientInfo": {"name": "business-assistant", "version": "1.0"},
                        },
                        "id": 1,
                    },
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                self._session_id = data.get("result", {}).get("sessionId")
                logger.info(f"MCP initialized: {self.server_url}")
                return True
        except Exception as e:
            logger.error(f"MCP initialization failed: {e}")
            return False

    def list_tools(self) -> list[dict]:
        """Fetch available tools from the MCP server."""
        if self._available_tools:
            return self._available_tools

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.server_url}/mcp",
                    json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                tools = resp.json().get("result", {}).get("tools", [])
                self._available_tools = tools
                return tools
        except Exception as e:
            logger.error(f"MCP list_tools failed: {e}")
            return []

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the MCP server."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.server_url}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": arguments},
                        "id": 3,
                    },
                    headers=self._headers(),
                )
                resp.raise_for_status()
                result = resp.json().get("result", {})

                # MCP returns content as array of {type, text} objects
                content_blocks = result.get("content", [])
                text_content = "\n".join(
                    block.get("text", "") for block in content_blocks if block.get("type") == "text"
                )

                return {"result": text_content or result}

        except httpx.TimeoutException:
            return {"error": f"MCP tool {tool_name} timed out after {self.timeout}s"}
        except Exception as e:
            logger.exception(f"MCP tool call failed: {tool_name}")
            return {"error": str(e)}


class MCPSubprocessClient:
    """
    Client for LOCAL MCP servers running as stdio subprocesses.
    Use this for sensitive internal tools that must not leave the server.

    Example: a custom MCP server that reads from your internal database
    without exposing raw SQL to the network.

    NOTE: For most Django use cases, calling tool functions directly
    (as done in mcp/tools.py) is simpler and equally effective.
    Use this only if you need strict MCP protocol compliance.
    """

    def __init__(self, command: list[str], env: dict = None):
        """
        command: e.g. ["python", "mcp_servers/db_server.py"]
        env: additional environment variables for the subprocess
        """
        self.command = command
        self.env = env
        self._process = None

    def start(self):
        import subprocess
        import os
        env = {**os.environ, **(self.env or {})}
        self._process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        logger.info(f"MCP subprocess started: {' '.join(self.command)}")

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        if not self._process:
            self.start()
        try:
            request = json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
                "id": 1,
            })
            self._process.stdin.write(request + "\n")
            self._process.stdin.flush()
            response_line = self._process.stdout.readline()
            response = json.loads(response_line)
            return response.get("result", {})
        except Exception as e:
            logger.exception(f"MCP subprocess tool call failed: {tool_name}")
            return {"error": str(e)}

    def stop(self):
        if self._process:
            self._process.terminate()
            self._process = None
