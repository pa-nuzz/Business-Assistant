"""
Django DB MCP Server — runs as a standalone stdio MCP server.

This exposes structured DB query tools over the MCP protocol.
It's intentionally READ-ONLY and structured — no raw SQL exposed.

Run standalone:
    python mcp/servers/db_mcp.py

Or connect via MCPSubprocessClient in your agent.
Uses the official `mcp` Python SDK.

Install: pip install mcp
"""
import sys
import os
import json
import asyncio

# Set up Django environment before any imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types


app = Server("django-db-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_business_profile",
            description="Get a user's business profile by user_id",
            inputSchema={
                "type": "object",
                "properties": {"user_id": {"type": "integer"}},
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="get_user_memory",
            description="Retrieve stored memory facts for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer"},
                    "category": {"type": "string", "default": "all"},
                },
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="save_memory",
            description="Save a memory fact for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer"},
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["user_id", "key", "value", "category"],
            },
        ),
        types.Tool(
            name="list_documents",
            description="List documents uploaded by a user",
            inputSchema={
                "type": "object",
                "properties": {"user_id": {"type": "integer"}},
                "required": ["user_id"],
            },
        ),
        types.Tool(
            name="search_document_chunks",
            description="Keyword search across document chunks",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "user_id": {"type": "integer"},
                },
                "required": ["query", "user_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Route tool calls to the appropriate Django ORM function."""
    from mcp.tools import execute_tool  # reuse existing tool implementations

    result = execute_tool(name, arguments)
    output = json.dumps(result, default=str, indent=2)

    return [types.TextContent(type="text", text=output)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
