# capivara-mcp
🦫 MCP server para dados do mercado financeiro brasileiro — PTAX, Selic, IPCA, Focus e mais, direto do Banco Central

## Instalação

```bash
uvx capivara-mcp
```

Ou instale globalmente:

```bash
uv tool install capivara-mcp
```

## Configuração no Claude Desktop

Adicione ao seu `claude_desktop_config.json`:

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

## Tools disponíveis

| Tool | Descrição |
|---|---|
| `get_ptax` | Cotações de câmbio (compra/venda) via PTAX |
| `get_selic` | Taxa Selic meta e efetiva |
| `get_inflacao` | Índices de inflação (IPCA e IGP-M) |
| `get_expectativas_mercado` | Expectativas do mercado (boletim Focus, 28 indicadores) |
