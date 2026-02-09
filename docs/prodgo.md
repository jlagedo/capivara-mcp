# Production Readiness Plan

Status: **Draft**

The core tool implementations are solid — clean patterns, consistent error handling, good Portuguese-first design. This document covers the gaps between "working prototype" and "production-ready MCP server," organized by priority.

---

## 1. Critical: Packaging & Distribution

Right now there's no way for users to install this easily. Claude Desktop needs a command to run the server, and currently that requires cloning the repo + `uv sync`.

**What to add:**

- `[project.scripts]` entry point in `pyproject.toml` so `uvx capivara-mcp` or `pipx run capivara-mcp` just works
- Claude Desktop config example in the README — users need the exact JSON snippet for `claude_desktop_config.json`
- Publish to PyPI so installation is `uv tool install capivara-mcp`

**Example Claude Desktop config users need:**

```json
{
  "mcpServers": {
    "capivara-mcp": {
      "command": "uvx",
      "args": ["capivara-mcp"]
    }
  }
}
```

---

## 2. Critical: Logging & Observability

The server currently has zero logging. When something goes wrong in Claude Desktop, users have no way to diagnose it. MCP servers running over stdio can't print to stdout (that's the protocol channel), so proper `logging` to stderr is required.

**What to add:**

- Python `logging` configured to stderr in `server.py`
- Log every tool invocation (indicator, params) at INFO level
- Log API errors at ERROR level with tracebacks
- Log startup with version info

---

## 3. High: Input Validation & Robustness

**Current gaps:**

- **No date validation** — `ptax.py` and `selic.py` pass user strings directly to the API. Invalid dates like `"2024-13-45"` produce cryptic `python-bcb` errors instead of clean user messages
- **No date range limits** — a user could request 20 years of daily PTAX data, causing memory/timeout issues
- **No timeout on API calls** — if BCB's API is slow/down, the tool hangs indefinitely, blocking Claude Desktop
- **Generic `Exception` catching** hides specific failure modes — catching `requests.Timeout` vs `requests.ConnectionError` vs `ValueError` separately would give much better error messages

---

## 4. High: Testing

No tests at all is the biggest risk for ongoing development.

**What to add:**

- **Unit tests with mocked API responses** — don't hit BCB on every test run. Use `pytest` + `respx` or `responses` to mock HTTP
- **Input validation tests** — bad dates, unsupported currencies, empty responses
- **Integration smoke test** — one test that actually hits BCB (marked `@pytest.mark.integration` so it's opt-in)
- **MCP protocol test** — use `mcp.client` to connect to the server and verify tool schemas are correct

---

## 5. High: Proper README & Documentation

The current README is just a title. Users evaluating an MCP server need:

- What data is available (tools table with examples)
- Installation instructions (uvx, pip, from source)
- Claude Desktop configuration JSON
- Example prompts that work well with each tool
- Screenshots/example outputs

---

## 6. Medium: Type Safety & Linting

- Add **`ruff`** for linting + formatting (one tool, fast, handles everything)
- Enable **`pyright`** or **`mypy`** — type hints are already there (`str | None`) but not checked
- Add `[tool.ruff]` and `[tool.pyright]` sections to `pyproject.toml`

---

## 7. Medium: CI/CD

A minimal GitHub Actions workflow:

- Run `ruff check` + `ruff format --check`
- Run `pytest` with mocked tests
- Optionally: type checking, build verification
- On tag: publish to PyPI automatically

---

## 8. Medium: Caching

BCB data doesn't change intra-day for most series. Repeated calls for the same data waste API calls and slow responses.

- Simple `functools.lru_cache` or `cachetools.TTLCache` with ~1hr TTL
- Especially impactful for `expectativas` which queries the heaviest endpoint

---

## 9. Low: Additional Tools (Feature Completeness)

The BCB API surface is much larger. Natural additions:

- **CDI** (series 12) — daily interbank rate, extremely common reference
- **IPCA-15** (series 7478) — preview inflation
- **Treasury yields** — NTN-B, LTN rates
- **Currency list** — tool to list available currencies for PTAX
- **Historical Focus medians** — time series of how expectations evolved

---

## 10. Low: SSE/Streamable HTTP Transport

stdio works great for Claude Desktop, but adding SSE transport as an option would expand reach to other MCP clients (web apps, remote setups). FastMCP supports this with minimal code changes.

---

## Implementation Order

Recommended sequence:

1. **Packaging** (`[project.scripts]`, PyPI-ready) — unblocks everything else
2. **Logging** to stderr — essential for debugging in production
3. **Input validation** + timeouts — prevents bad user experience
4. **README** with install + config instructions — users can't adopt what they can't set up
5. **Tests** + **CI** — safety net for all future changes
6. **Ruff + type checking** — catches bugs early
7. **Caching** — performance improvement
8. **More tools** — feature expansion
