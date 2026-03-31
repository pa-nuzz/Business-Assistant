"""
Document MCP Server — handles document operations via MCP protocol.

Tools exposed:
  - get_document_summary(doc_id, user_id)
  - search_documents(query, user_id, doc_id?)
  - list_documents(user_id)

This runs as a subprocess MCP server (stdio).
Django environment is initialized on startup.
"""
import sys
import os
import json
import asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types


app = Server("document-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_document_summary",
            description=(
                "Returns the pre-generated AI summary of a document. "
                "Fast and cheap — always try this before search_documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"},
                    "user_id": {"type": "integer"},
                },
                "required": ["doc_id", "user_id"],
            },
        ),
        types.Tool(
            name="search_documents",
            description=(
                "Keyword search across document chunks. Returns top matching sections. "
                "Use for specific questions about document content."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "user_id": {"type": "integer"},
                    "doc_id": {"type": "string", "description": "Optional: limit to one document"},
                },
                "required": ["query", "user_id"],
            },
        ),
        types.Tool(
            name="list_documents",
            description="List all documents uploaded by a user.",
            inputSchema={
                "type": "object",
                "properties": {"user_id": {"type": "integer"}},
                "required": ["user_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    from mcp.tools import execute_tool
    result = execute_tool(name, arguments)
    return [types.TextContent(type="text", text=json.dumps(result, default=str, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
