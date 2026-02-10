# Fase 2 — Implementação de APIs de prioridade alta e média

Plano de expansão do capivara-mcp com novas tools para dados do BCB.

**Referência:** [docs/bcb_api.md](bcb_api.md)

---

## Escopo

### Prioridade Alta

| # | Tool | API | Séries/Endpoints | Esforço |
|---|------|-----|------------------|---------|
| 1 | Expandir `get_inflacao` | SGS | CDI (12), IPCA-15 (7478), INPC (188) | Baixo |
| 2 | Novo `get_atividade_economica` | SGS | PIB mensal (4380), Dívida/PIB (4513), Resultado primário (5793) | Baixo |
| 3 | Novo `get_expectativas_mensais` | Expectativas | `ExpectativaMercadoMensais` | Médio |
| 4 | Novo `get_expectativas_selic` | Expectativas | `ExpectativasMercadoSelic` | Médio |

### Prioridade Média

| # | Tool | API | Endpoints | Esforço |
|---|------|-----|-----------|---------|
| 5 | Novo `get_taxa_juros` | TaxaJuros OData | `TaxasJurosMensalPorMes` | Médio |
| 6 | Novo `get_expectativas_inflacao12m` | Expectativas | `ExpectativasMercadoInflacao12Meses` | Médio |
| 7 | Novo `get_expectativas_top5` | Expectativas | `ExpectativasMercadoTop5Anuais` | Médio |

---

## Detalhamento por tarefa

### 1. Expandir `get_inflacao` — CDI, IPCA-15, INPC

**Arquivo:** `src/capivara_mcp/tools/inflacao.py`

**Mudanças:**
- Adicionar séries ao `_SERIES`:
  ```python
  _SERIES = {
      "IPCA": 433,
      "IGP-M": 189,
      "CDI": 12,
      "IPCA-15": 7478,
      "INPC": 188,
  }
  ```
- Atualizar a mensagem de erro de validação do parâmetro `indice` para listar as novas opções
- Atualizar a docstring do `get_inflacao` para documentar os novos índices

**Testes:** `tests/test_inflacao.py`
- Adicionar casos de sucesso para CDI, IPCA-15 e INPC
- Testar validação: `indice="CDI"` aceito, `indice="cdi"` aceito (case-insensitive)

**Nota:** CDI é tecnicamente uma taxa e não um índice de inflação, mas compartilha o mesmo padrão SGS de série temporal mensal. Manter no mesmo tool evita criar um módulo separado para uma única série. A docstring deve refletir que o tool cobre "índices de inflação e taxas de referência".

---

### 2. Novo tool `get_atividade_economica`

**Arquivo novo:** `src/capivara_mcp/tools/atividade.py`

**Justificativa para módulo separado:** PIB e indicadores fiscais são semanticamente distintos de inflação/taxas. Agrupá-los em um tool próprio melhora a descoberta pelo LLM.

**Séries:**
```python
_SERIES = {
    "PIB mensal": 4380,
    "Dívida bruta/PIB": 4513,
    "Resultado primário": 5793,
}
```

**Assinatura:**
```python
async def get_atividade_economica(
    indicador: str = "PIB mensal",
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> str:
```

**Padrão:** Idêntico ao `get_inflacao` — validação de indicador, parse de datas, `_fetch` com `ThreadPoolExecutor`, `sgs.get()`, tratamento de erros. Max 1825 dias (dados mensais).

**Resposta JSON:**
```json
{
  "indicador": "PIB mensal",
  "periodo": {"inicio": "2024-01-01", "fim": "2025-01-01"},
  "valores": [
    {"data": "2024-01-01", "PIB mensal": 123.45}
  ]
}
```

**Registro:** Adicionar em `server.py`:
```python
from capivara_mcp.tools.atividade import get_atividade_economica
mcp.tool()(get_atividade_economica)
```

**Testes:** `tests/test_atividade.py`
- Sucesso com cada indicador
- Validação de indicador inválido
- Timeout, erro de conexão, erro inesperado
- DataFrame vazio

---

### 3. Novo tool `get_expectativas_mensais`

**Arquivo:** `src/capivara_mcp/tools/expectativas.py` (mesmo módulo, nova função)

**Endpoint:** `ExpectativaMercadoMensais`

**Diferença do anuais:** `DataReferencia` é `"MM/YYYY"` em vez de ano inteiro. Campos são os mesmos (Indicador, Data, DataReferencia, Media, Mediana, Minimo, Maximo, baseCalculo).

**Indicadores suportados:** Mesmo set `_INDICADORES` já existente (reutilizar).

**Assinatura:**
```python
async def get_expectativas_mensais(
    indicador: str = "IPCA",
    top: int = 10,
) -> str:
```

**Implementação:**
- Nova função `_fetch_expectativas_mensais(indicador, top)` que usa endpoint `ExpectativaMercadoMensais`
- Filtro: `ep.Indicador == indicador`, `ep.baseCalculo == 0`
- Ordenação: `ep.Data.desc()`
- Select: mesmos campos do anuais
- Renomeação de colunas: mesmo mapeamento `colunas` existente

**Resposta JSON:**
```json
{
  "indicador": "IPCA",
  "frequencia": "mensal",
  "expectativas": [
    {
      "indicador": "IPCA",
      "data_pesquisa": "2025-01-10",
      "periodo_referencia": "01/2025",
      "media": 0.45,
      "mediana": 0.44,
      "minimo": 0.30,
      "maximo": 0.60
    }
  ]
}
```

**Registro:** `mcp.tool()(get_expectativas_mensais)` em `server.py`.

**Testes:** Adicionar classes em `tests/test_expectativas.py`
- Factory `make_expectativas_mensais_df()` em `conftest.py` (DataReferencia como string "MM/YYYY")
- Sucesso, DataFrame vazio, indicador inválido, timeout, connection error

---

### 4. Novo tool `get_expectativas_selic`

**Arquivo:** `src/capivara_mcp/tools/expectativas.py`

**Endpoint:** `ExpectativasMercadoSelic`

**Diferença:** Campos específicos — inclui `Reuniao` (data da reunião do COPOM) e `DataReferencia` é a data da reunião. Não tem campo `Indicador` (é sempre Selic).

**Assinatura:**
```python
async def get_expectativas_selic(
    top: int = 10,
) -> str:
```

**Implementação:**
- Nova função `_fetch_expectativas_selic(top)` com endpoint `ExpectativasMercadoSelic`
- Filtro: `ep.baseCalculo == 0`
- Ordenação: `ep.Data.desc()`
- Select: `ep.Data, ep.Reuniao, ep.Media, ep.Mediana, ep.Minimo, ep.Maximo`

**Resposta JSON:**
```json
{
  "indicador": "Selic",
  "frequencia": "por_reuniao",
  "expectativas": [
    {
      "data_pesquisa": "2025-01-10",
      "reuniao": "R45/2025",
      "media": 14.75,
      "mediana": 14.75,
      "minimo": 14.25,
      "maximo": 15.25
    }
  ]
}
```

**Testes:** Nova classe em `tests/test_expectativas.py`
- Factory `make_expectativas_selic_df()` em `conftest.py`
- Sucesso, DataFrame vazio, timeout, connection error

---

### 5. Novo tool `get_taxa_juros`

**Arquivo novo:** `src/capivara_mcp/tools/taxa_juros.py`

**API:** `bcb.TaxaJuros` — OData, endpoint `TaxasJurosMensalPorMes`

**Assinatura:**
```python
async def get_taxa_juros(
    mes: str,
    modalidade: str | None = None,
    top: int = 20,
) -> str:
```

**Parâmetros:**
- `mes`: Mês no formato `"MMM-YYYY"` (ex: `"Jan-2025"`). Obrigatório.
- `modalidade`: Filtro opcional por modalidade de crédito (ex: `"CHEQUE ESPECIAL"`)
- `top`: Limite de resultados

**Implementação:**
```python
from bcb import TaxaJuros

def _fetch_taxa_juros(mes: str, modalidade: str | None, top: int) -> pd.DataFrame:
    tj = TaxaJuros()
    ep = tj.get_endpoint("TaxasJurosMensalPorMes")
    query = ep.query().filter(ep.Mes == mes)
    if modalidade:
        query = query.filter(ep.Modalidade == modalidade)
    return query.orderby(ep.TaxaJurosAoAno.asc()).limit(top).collect()
```

**Resposta JSON:**
```json
{
  "mes": "Jan-2025",
  "taxas": [
    {
      "instituicao": "CAIXA ECONOMICA FEDERAL",
      "modalidade": "FINANCIAMENTO IMOBILIARIO...",
      "taxa_mensal": 0.39,
      "taxa_anual": 4.75,
      "cnpj8": "00360305"
    }
  ]
}
```

**Colunas renomeadas:**
```python
{
    "InstituicaoFinanceira": "instituicao",
    "Modalidade": "modalidade",
    "TaxaJurosAoMes": "taxa_mensal",
    "TaxaJurosAoAno": "taxa_anual",
    "cnpj8": "cnpj8",
}
```

**Registro:** `mcp.tool()(get_taxa_juros)` em `server.py`.

**Testes:** `tests/test_taxa_juros.py`
- Factory `make_taxa_juros_df()` em `conftest.py`
- Sucesso com e sem filtro de modalidade
- Mês em formato inválido
- DataFrame vazio, timeout, connection error

---

### 6. Novo tool `get_expectativas_inflacao12m`

**Arquivo:** `src/capivara_mcp/tools/expectativas.py`

**Endpoint:** `ExpectativasMercadoInflacao12Meses`

**Indicadores suportados:** Subconjunto de `_INDICADORES` — apenas indicadores de inflação:
```python
_INDICADORES_INFLACAO = {"IPCA", "IGP-M", "INPC", "IGP-DI", "IPCA Administrados", "IPCA Livres", "IPCA Serviços", "IPCA Alimentação no domicílio", "IPCA Bens industrializados"}
```

**Assinatura:**
```python
async def get_expectativas_inflacao12m(
    indicador: str = "IPCA",
    top: int = 10,
) -> str:
```

**Implementação:** Segue o padrão do `get_expectativas_mercado`. Filtro `baseCalculo == 0`, `ep.Indicador == indicador`. Campos: `Indicador, Data, Media, Mediana, Minimo, Maximo, Suavizada` (campo extra `Suavizada` indica se é a série suavizada).

**Resposta JSON:**
```json
{
  "indicador": "IPCA",
  "horizonte": "12_meses",
  "expectativas": [
    {
      "indicador": "IPCA",
      "data_pesquisa": "2025-01-10",
      "media": 4.50,
      "mediana": 4.48,
      "minimo": 3.80,
      "maximo": 5.20,
      "suavizada": "S"
    }
  ]
}
```

**Testes:** Classes adicionais em `tests/test_expectativas.py`.

---

### 7. Novo tool `get_expectativas_top5`

**Arquivo:** `src/capivara_mcp/tools/expectativas.py`

**Endpoint:** `ExpectativasMercadoTop5Anuais`

**Assinatura:**
```python
async def get_expectativas_top5(
    indicador: str = "IPCA",
    top: int = 10,
) -> str:
```

**Implementação:** Mesmo padrão. Diferença: campos incluem `tipoCalculo` ("C" = curto prazo, "L" = longo prazo). Usa `_INDICADORES` existente.

**Resposta JSON:**
```json
{
  "indicador": "IPCA",
  "tipo": "top5_anual",
  "expectativas": [
    {
      "indicador": "IPCA",
      "data_pesquisa": "2025-01-10",
      "periodo_referencia": "2025",
      "tipo_calculo": "C",
      "media": 4.50,
      "mediana": 4.48,
      "minimo": 3.80,
      "maximo": 5.20
    }
  ]
}
```

**Testes:** Classes adicionais em `tests/test_expectativas.py`.

---

## Ordem de execução

```
Tarefa 1 (expandir inflacao)
    │
    ├── Tarefa 2 (atividade econômica)  ← pode ser paralela com 1
    │
    ▼
Tarefa 3 (expectativas mensais)
    │
    ├── Tarefa 4 (expectativas selic)   ← pode ser paralela com 3
    │
    ▼
Tarefa 5 (taxa de juros)
    │
    ├── Tarefa 6 (inflação 12m)         ← pode ser paralela com 5
    │
    ├── Tarefa 7 (top5)                 ← pode ser paralela com 5
    │
    ▼
Registrar tudo em server.py + testes de integração
```

---

## Convenções a seguir (do codebase existente)

1. **Retorno sempre `str` (JSON)** — nunca dicts ou exceções
2. **Erros com chave `"erro"`** — usar `erro_json()` de `_validation.py`
3. **Datas ISO `YYYY-MM-DD`** — strings na entrada e saída
4. **Colunas snake_case** em português na saída JSON
5. **Docstrings em português** — descrevendo o que o tool faz
6. **`ThreadPoolExecutor`** com timeout para chamadas SGS (bloqueantes)
7. **httpx exceptions** para chamadas OData (Expectativas, TaxaJuros)
8. **Testes unitários** mockando `_fetch_*`, sem hits na API real
9. **Testes de integração** com `@pytest.mark.integration` para smoke tests

---

## Arquivos tocados

| Arquivo | Ação |
|---------|------|
| `src/capivara_mcp/tools/inflacao.py` | Modificar — adicionar CDI, IPCA-15, INPC |
| `src/capivara_mcp/tools/atividade.py` | **Criar** — PIB mensal, Dívida/PIB, Resultado primário |
| `src/capivara_mcp/tools/expectativas.py` | Modificar — adicionar 4 novas funções |
| `src/capivara_mcp/tools/taxa_juros.py` | **Criar** — taxas de juros por instituição |
| `src/capivara_mcp/server.py` | Modificar — registrar 5 novos tools |
| `tests/conftest.py` | Modificar — adicionar factories para novos DataFrames |
| `tests/test_inflacao.py` | Modificar — testes para novos índices |
| `tests/test_atividade.py` | **Criar** — testes do tool de atividade |
| `tests/test_expectativas.py` | Modificar — testes para 4 novos tools |
| `tests/test_taxa_juros.py` | **Criar** — testes do tool de taxa de juros |
| `tests/test_integration.py` | Modificar — smoke tests dos novos tools |
| `docs/bcb_api.md` | Modificar — atualizar status para **Implementado** |
