"""MCP protocol tests — verify tool schemas via real server subprocess."""

from __future__ import annotations

import sys

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.fixture
def server_params():
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "capivara_mcp.server"],
    )


@pytest.mark.asyncio
async def test_list_tools_returns_all_four(server_params):
    async with stdio_client(server_params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            tool_names = {tool.name for tool in result.tools}
            assert tool_names == {
                "get_ptax",
                "get_selic",
                "get_inflacao",
                "get_expectativas_mercado",
            }


@pytest.mark.asyncio
async def test_tools_have_descriptions(server_params):
    async with stdio_client(server_params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            for tool in result.tools:
                assert tool.description, f"Tool {tool.name} has no description"
                assert len(tool.description) > 10


@pytest.mark.asyncio
async def test_tools_have_valid_input_schemas(server_params):
    async with stdio_client(server_params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            for tool in result.tools:
                schema = tool.inputSchema
                assert schema["type"] == "object"
                assert "properties" in schema


@pytest.mark.asyncio
async def test_ptax_schema_params(server_params):
    async with stdio_client(server_params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            ptax = next(t for t in result.tools if t.name == "get_ptax")
            props = ptax.inputSchema["properties"]
            assert "moeda" in props
            assert "data_inicio" in props
            assert "data_fim" in props


@pytest.mark.asyncio
async def test_expectativas_schema_params(server_params):
    async with stdio_client(server_params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            exp = next(t for t in result.tools if t.name == "get_expectativas_mercado")
            props = exp.inputSchema["properties"]
            assert "indicador" in props
            assert "top" in props
