"""
Search MCP Server — web search via Brave API (DuckDuckGo fallback).

This can run as:
  A) A standalone stdio subprocess (MCPSubprocessClient)
  B) A standalone HTTP server for other agents to call

Free tier: Brave gives 2000 searches/month free.
No key? DuckDuckGo fallback handles it silently.
"""
import os
import json
import asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types


app = Server("search-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="brave_search",
            description=(
                "Search the web for current information: market data, competitors, "
                "news, trends, pricing, regulations. Returns top results with titles, "
                "URLs, and snippets."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query. Be specific for better results.",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results (1-5). Default: 3.",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "brave_search":
        from mcp.tools import brave_search
        result = brave_search(
            query=arguments["query"],
            num_results=arguments.get("num_results", 3),
        )
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
