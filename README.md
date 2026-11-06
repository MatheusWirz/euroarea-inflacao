# Relatório Automatizado de Inflação — Zona do Euro

Relatório em HTML, gerado com [Quarto](https://quarto.org/) e [Plotly](https://plotly.com/python/), que busca na API da Eurostat os dados do Índice Harmonizado de Preços ao Consumidor (HICP) e monta os gráficos automaticamente a cada execução.

## O que o relatório mostra

- **Panorama:** inflação anual, variação mensal e categoria com maior alta, além de um botão para baixar a série em CSV.
- **Evolução do índice geral:** variação anual (linha) e mensal (barras).
- **Quem está puxando os preços:** incidência (em pontos percentuais) de cada grupo da cesta na inflação anual.
- **Núcleo, energia e serviços:** comparação das séries ao longo do tempo.
- **Mapa de calor:** inflação anual por categoria e mês.

## Estrutura do projeto

| Arquivo | Função |
|---|---|
| `report.qmd` | Documento Quarto com o texto e as células que geram o relatório |
| `functions.py` | Requisições à Eurostat, tratamento dos dados e funções de gráficos |
| `dicts.py` | Dicionário com os códigos dos datasets de inflação por categoria |
| `styles.css` | Estilo do HTML (branco e azul-marinho) |
| `requirements.txt` | Dependências Python |

## Como executar

### 1. Pré-requisitos

- [Python](https://www.python.org/downloads/) 3.10 ou superior
- [Quarto](https://quarto.org/docs/get-started/) 1.4 ou superior
- Conexão com a internet (os dados são buscados na Eurostat a cada renderização)

### 2. Clonar e instalar as dependências

```bash
git clone <url-do-repositorio>
cd euro-inflation

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Gerar o relatório

```bash
quarto render report.qmd
```

O arquivo `report.html` é criado na raiz do projeto. Ele é autocontido: dá para abrir direto no navegador ou enviar por e-mail.

> A primeira execução leva cerca de um minuto, porque são feitas uma requisição por categoria (22 no total).

Para visualizar com recarregamento automático enquanto edita:

```bash
quarto preview report.qmd
```

## Configuração

- **Área geográfica e unidades** estão em `functions.py` (`geo_code = "EA21"` e `unit_code = ["PCH_M12", "PCH_M1"]`).
- **Categorias** vêm de `dicts.py`; qualquer item adicionado ao dicionário entra automaticamente no relatório.
- **Pesos da cesta** (usados na incidência) vêm do dataset `prc_hicp_inw`, que ainda só publica a zona do euro com 20 países (`EA20`). A conta de incidência é uma aproximação (peso × variação anual), então a soma pode diferir um pouco da inflação oficial.

## Ferramentas e bibliotecas

| Ferramenta | Uso |
|---|---|
| [Quarto](https://quarto.org/) | Renderização do relatório `.qmd` em HTML |
| [Python](https://www.python.org/) | Linguagem de execução das análises |
| [eurostat](https://pypi.org/project/eurostat/) | Acesso à API da Eurostat |
| [pandas](https://pandas.pydata.org/) | Manipulação e transformação dos dados |
| [Plotly](https://plotly.com/python/) | Gráficos interativos |
| [ipykernel](https://pypi.org/project/ipykernel/) | Kernel Jupyter usado pelo Quarto para executar o Python |

## Fonte dos dados

[Eurostat](https://ec.europa.eu/eurostat) — HICP (datasets `teicp*` e `prc_hicp_inw`).
