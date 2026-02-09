"""Capivara MCP — servidor MCP para dados do mercado financeiro brasileiro.

Entry point do servidor. Registra os tools e inicia o transporte stdio.
"""

import logging
import sys
from importlib.metadata import version

from mcp.server.fastmcp import FastMCP

from capivara_mcp.tools.expectativas import get_expectativas_mercado
from capivara_mcp.tools.inflacao import get_inflacao
from capivara_mcp.tools.ptax import get_ptax
from capivara_mcp.tools.selic import get_selic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("capivara-mcp")

mcp = FastMCP("capivara-mcp")

# Registrar tools
mcp.tool()(get_ptax)
mcp.tool()(get_selic)
mcp.tool()(get_inflacao)
mcp.tool()(get_expectativas_mercado)


def main():
    pkg_version = version("capivara-mcp")
    logger.info("Iniciando capivara-mcp v%s", pkg_version)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
