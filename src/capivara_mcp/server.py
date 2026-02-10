"""Capivara MCP — servidor MCP para dados do mercado financeiro brasileiro.

Entry point do servidor. Registra os tools e inicia o transporte stdio.
"""

import logging
import sys
from importlib.metadata import version

from mcp.server.fastmcp import FastMCP

from capivara_mcp.tools.atividade import get_atividade_economica
from capivara_mcp.tools.expectativas import (
    get_expectativas_inflacao12m,
    get_expectativas_mensais,
    get_expectativas_mercado,
    get_expectativas_selic,
    get_expectativas_top5,
)
from capivara_mcp.tools.inflacao import get_inflacao
from capivara_mcp.tools.ptax import get_ptax
from capivara_mcp.tools.selic import get_selic
from capivara_mcp.tools.taxa_juros import get_taxa_juros

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
mcp.tool()(get_atividade_economica)
mcp.tool()(get_expectativas_mercado)
mcp.tool()(get_expectativas_mensais)
mcp.tool()(get_expectativas_selic)
mcp.tool()(get_expectativas_inflacao12m)
mcp.tool()(get_expectativas_top5)
mcp.tool()(get_taxa_juros)


def main():
    pkg_version = version("capivara-mcp")
    logger.info("Iniciando capivara-mcp v%s", pkg_version)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
