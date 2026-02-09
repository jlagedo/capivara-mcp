# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

capivara-mcp is an MCP (Model Context Protocol) server that exposes Brazilian Central Bank (BCB) financial data as tools. It wraps BCB's public APIs (SGS, PTAX OData, Expectativas) using `python-bcb` and serves them over stdio transport via FastMCP.

## Commands

```bash
# Install dependencies
uv sync

# Run the MCP server (stdio transport)
python -m capivara_mcp.server

# Or from project root
cd src && python -m capivara_mcp.server
```

No test framework or linter is currently configured.

## Architecture

**Entry point:** `src/capivara_mcp/server.py` — creates a `FastMCP("capivara-mcp")` instance, registers all tools, and runs with stdio transport.

**Tools** live in `src/capivara_mcp/tools/`, one module per BCB API endpoint:

| Module | Tool Function | BCB API | Purpose |
|---|---|---|---|
| `ptax.py` | `get_ptax` | PTAX OData | Exchange rate quotations (buy/sell) |
| `selic.py` | `get_selic` | SGS (series 432, 11) | Selic target & effective rates |
| `inflacao.py` | `get_inflacao` | SGS (series 433, 189) | IPCA and IGP-M inflation indices |
| `expectativas.py` | `get_expectativas_mercado` | Expectativas | Focus bulletin market expectations (28 indicators) |

**Pattern for adding new tools:**
1. Create a new module in `tools/` with an async function that returns a JSON string
2. Register it in `server.py` with `mcp.tool()(your_function)`

**Key conventions:**
- All tools return JSON strings (not dicts) — use `json.dumps(..., ensure_ascii=False)` for Portuguese characters
- Dates use ISO format (YYYY-MM-DD) as strings
- Data flows through pandas DataFrames; datetime columns are converted to ISO strings before serialization
- Error responses are JSON strings with an `"erro"` key, never raised exceptions
- Docstrings and user-facing text are in Portuguese

## Dependencies

- **mcp[cli]**: FastMCP framework for building the MCP server
- **python-bcb**: Python wrapper for BCB APIs (SGS, PTAX, Expectativas)
- Python 3.11+ required (see `.python-version`)
- Build backend: hatchling
