# APIs do Banco Central disponíveis via python-bcb

Referência completa das interfaces do BCB acessíveis pela biblioteca `python-bcb`. Organizadas por relevância para análise econômica e financeira.

Legenda de status: **Implementado** | Disponível

---

## Tier 1 — Dados macroeconômicos essenciais

### PTAX (Câmbio) — **Implementado**

Cotações oficiais de câmbio do Banco Central.

| Endpoint | Descrição |
|---|---|
| `CotacaoMoedaPeriodo` | Cotações de compra/venda por período **[em uso]** |
| `CotacaoDolarDia` | Cotação do dólar em data específica |
| `CotacaoDolarPeriodo` | Cotações do dólar por período |
| `CotacaoMoedaDia` | Cotação de moeda específica em data |
| `CotacaoMoedaPeriodoFechamento` | Cotações de fechamento por período |
| `CotacaoMoedaAberturaOuIntermediario` | Cotações de abertura e intermediárias |
| `Moedas` | Lista de moedas disponíveis |

**Classe:** `bcb.PTAX`
**URL base:** `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/`

---

### SGS — Sistema Gerenciador de Séries Temporais — **Implementado parcialmente**

Acesso a milhares de séries temporais do BCB por código numérico.

| Série | Código | Status |
|---|---|---|
| Selic meta | 432 | **Implementado** |
| Selic efetiva (over) | 11 | **Implementado** |
| IPCA | 433 | **Implementado** |
| IGP-M | 189 | **Implementado** |
| CDI | 12 | Disponível |
| IPCA-15 | 7478 | Disponível |
| INPC | 188 | Disponível |
| IGP-DI | 190 | Disponível |
| Dívida pública/PIB | 4513 | Disponível |
| Resultado primário | 5793 | Disponível |
| PIB mensal | 4380 | Disponível |

**Módulo:** `bcb.sgs`
**Funções:** `sgs.get(codes, start, end, last, freq)`, `sgs.get_json(code, start, end, last)`

> O SGS possui mais de 30.000 séries. Qualquer código pode ser consultado com `sgs.get()`.

---

### Expectativas de Mercado (Boletim Focus) — **Implementado parcialmente**

Expectativas do mercado financeiro coletadas pelo BCB semanalmente. Fonte principal para projeções macroeconômicas no Brasil.

| Endpoint | Descrição | Status |
|---|---|---|
| `ExpectativasMercadoAnuais` | Expectativas anuais | **Implementado** (28 indicadores) |
| `ExpectativaMercadoMensais` | Expectativas mensais | Disponível |
| `ExpectativasMercadoTrimestrais` | Expectativas trimestrais | Disponível |
| `ExpectativasMercadoSelic` | Expectativas específicas para a Selic | Disponível |
| `ExpectativasMercadoInflacao12Meses` | Inflação acumulada 12 meses | Disponível |
| `ExpectativasMercadoInflacao24Meses` | Inflação acumulada 24 meses | Disponível |
| `ExpectativasMercadoTop5Anuais` | Top 5 instituições — anuais | Disponível |
| `ExpectativasMercadoTop5Mensais` | Top 5 instituições — mensais | Disponível |
| `ExpectativasMercadoTop5Selic` | Top 5 instituições — Selic | Disponível |
| `ExpectativasMercadoTop5Inflacao12Meses` | Top 5 — inflação 12 meses | Disponível |
| `ExpectativasMercadoTop5Inflacao24Meses` | Top 5 — inflação 24 meses | Disponível |
| `ExpectativaMercadoTop5Trimestral` | Top 5 — trimestrais | Disponível |
| `DatasReferencia` | Datas de referência disponíveis | Disponível |

**Classe:** `bcb.Expectativas`
**URL base:** `https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/`

---

## Tier 2 — Dados financeiros de alta relevância

### TaxaJuros (Taxas de Juros por Instituição)

Taxas de juros praticadas pelas instituições financeiras em operações de crédito. Médias de 5 dias úteis. Complementa a Selic com dados reais do mercado de crédito.

| Endpoint | Descrição |
|---|---|
| `ConsultaUnificada` | Consulta unificada de todas as taxas |
| `TaxasJurosMensalPorMes` | Taxas mensais consolidadas |
| `TaxasJurosDiariaPorInicioPeriodo` | Taxas diárias por período |
| `ParametrosConsulta` | Parâmetros disponíveis para consulta |
| `ConsultaDatas` | Datas disponíveis |

**Classe:** `bcb.TaxaJuros`
**URL base:** `https://olinda.bcb.gov.br/olinda/servico/taxaJuros/versao/v2/odata/`

**Casos de uso:** spread bancário, custo de crédito pessoal/empresarial, comparação entre instituições.

---

### SPI (Sistema de Pagamentos Instantâneos — Pix)

Estatísticas do Pix: volumes, valores liquidados, disponibilidade do sistema.

| Endpoint | Descrição |
|---|---|
| `PixLiquidadosAtual` | Transações Pix liquidadas (atual) |
| `PixLiquidadosIntradia` | Transações Pix liquidadas intraday |
| `PixDisponibilidadeSPI` | Disponibilidade do sistema SPI |
| `PixInterrupcaoSPI` | Interrupções do sistema |
| `PixRemuneracaoContaPI` | Remuneração da conta PI |

**Classe:** `bcb.SPI`
**URL base:** `https://olinda.bcb.gov.br/olinda/servico/SPI/versao/v1/odata/`

**Casos de uso:** volume transacional do Pix, monitoramento de disponibilidade, análise de adoção.

---

### DinheiroCirculacao (Dinheiro em Circulação)

Quantidade de cédulas e moedas em circulação, atualizado diariamente. Dados por denominação e família.

| Endpoint | Descrição |
|---|---|
| `informacoes_diarias` | Totais diários em circulação |
| `informacoes_diarias_com_categoria` | Totais diários por denominação e categoria |

**Classe:** `bcb.DinheiroCirculacao`
**URL base:** `https://olinda.bcb.gov.br/olinda/servico/mecir_dinheiro_em_circulacao/versao/v1/odata/`

**Casos de uso:** base monetária, análise de preferência por denominações, tendências de uso de dinheiro físico.

---

### Inadimplência Regional (SGS — Regional Economy)

Taxas de inadimplência (NPL) por estado e região, segmentadas por pessoa física, jurídica ou total.

| Função | Descrição |
|---|---|
| `get_non_performing_loans(states_or_region, mode)` | Séries de inadimplência por UF/região |
| `get_non_performing_loans_codes(states_or_region, mode)` | Códigos SGS para inadimplência |

**Módulo:** `bcb.sgs.regional_economy`
**Modos:** `'total'`, `'pf'` (pessoa física), `'pj'` (pessoa jurídica)
**Cobertura:** 27 estados + 5 regiões

**Casos de uso:** risco de crédito regional, análise geográfica de inadimplência, comparação entre estados.

---

## Tier 3 — Dados setoriais e institucionais

### IFDATA (Dados de Instituições Financeiras)

Dados selecionados dos balanços trimestrais das instituições financeiras: ativos, passivos, capital, operações.

| Endpoint | Descrição |
|---|---|
| `IfDataValores` | Valores financeiros por instituição |
| `IfDataCadastro` | Dados cadastrais |
| `ListaDeRelatorio` | Lista de relatórios disponíveis |

**Classe:** `bcb.IFDATA`
**Atualização:** Trimestral (60–90 dias após fechamento)

**Casos de uso:** análise de balanço de bancos, concentração bancária, ranking de instituições.

---

### MercadoImobiliario (Mercado Imobiliário)

Estatísticas de crédito imobiliário e mercado habitacional. Mais de 4.000 séries mensais com detalhamento por UF.

| Endpoint | Descrição |
|---|---|
| `mercadoimobiliario` | Dados consolidados do mercado imobiliário |

**Classe:** `bcb.MercadoImobiliario`

**Casos de uso:** crédito habitacional, análise do mercado imobiliário por estado, tendências de financiamento.

---

### EstatisticasSTR (Sistema de Transferência de Reservas)

Estatísticas do STR — sistema de liquidação bruta em tempo real do BCB.

| Endpoint | Descrição |
|---|---|
| `GiroEvolucaoDiaria` | Evolução diária do giro |
| `GiroDetalhamento` | Detalhamento do giro |
| `TEDEvolucaoDiaria` | Evolução diária de TEDs |
| `TEDHistograma21Dias` | Histograma de TEDs (21 dias) |
| `PagamentosIntradia` | Pagamentos intraday |
| `RedescontoBCBIntradia` | Redesconto intraday |
| `PortabilidadeDeCredito` | Portabilidade de crédito (geral) |
| `PortabilidadeDeCreditoPessoaNatural` | Portabilidade — pessoa física |
| `PortabilidadeDeCreditoPJEArrendamentoMercantil` | Portabilidade — PJ e leasing |
| `EstatisticasTransferenciasLiquidacaoDocumentosComCodigoBarras` | Liquidação de boletos |

**Classe:** `bcb.EstatisticasSTR`

**Casos de uso:** volume de TEDs, análise do sistema de pagamentos, portabilidade de crédito.

---

## Tier 4 — Dados de tarifas e atendimento

### TarifasBancariasPorInstituicaoFinanceira

| Endpoint | Descrição |
|---|---|
| `ListaTarifasPorInstituicaoFinanceira` | Tarifas cobradas por instituição |
| `ListaInstituicoesDeGrupoConsolidado` | Instituições por grupo |
| `GruposConsolidados` | Lista de grupos consolidados |

**Classe:** `bcb.TarifasBancariasPorInstituicaoFinanceira`

---

### TarifasBancariasPorServico

| Endpoint | Descrição |
|---|---|
| `ListaValoresServicoBancario` | Valores mín/máx/médio por serviço |
| `GruposConsolidados` | Lista de grupos consolidados |

**Classe:** `bcb.TarifasBancariasPorServico`

---

### PostosAtendimentoEletronicoPorInstituicaoFinanceira

| Endpoint | Descrição |
|---|---|
| `PostosAtendimentoEletronico` | Caixas eletrônicos por instituição |

**Classe:** `bcb.PostosAtendimentoEletronicoPorInstituicaoFinanceira`

---

### PostosAtendimentoCorrespondentesPorInstituicaoFinanceira

| Endpoint | Descrição |
|---|---|
| `Correspondentes` | Correspondentes bancários por instituição e município |

**Classe:** `bcb.PostosAtendimentoCorrespondentesPorInstituicaoFinanceira`

---

## Módulo auxiliar: Currency

Acesso alternativo a câmbio direto do site PTAX (não OData).

| Função | Descrição |
|---|---|
| `get(symbols, start, end, side, groupby)` | Séries históricas de câmbio |
| `get_currency_list()` | Lista de moedas disponíveis |

**Módulo:** `bcb.currency`
**Parâmetro `side`:** `'ask'`, `'bid'`, `'both'`

---

## Classe genérica: ODataAPI

Para acessar qualquer API OData do BCB não coberta pelas classes acima.

```python
from bcb import ODataAPI
api = ODataAPI("https://olinda.bcb.gov.br/olinda/servico/<servico>/versao/v1/odata/")
ep = api.get_endpoint("<endpoint>")
df = ep.query().collect()
```

---

## Padrão de uso

Todas as APIs OData seguem o mesmo padrão:

```python
from bcb import <Classe>

api = <Classe>()
ep = api.get_endpoint("<endpoint>")
df = (
    ep.query()
    .filter(ep.Campo == valor)
    .orderby(ep.Campo.desc())
    .select(ep.Campo1, ep.Campo2)
    .limit(100)
    .collect()
)
```

O SGS usa interface diferente:

```python
from bcb import sgs
df = sgs.get({"nome": codigo}, start="2024-01-01", end="2024-12-31")
```
