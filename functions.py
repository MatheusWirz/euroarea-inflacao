import eurostat
import pandas as pd
import plotly.graph_objects as go

from dicts import hicp_categories

# Área geográfica e unidades de medida usadas em todas as requisições
geo_code = "EA21"
unit_code = ["PCH_M12", "PCH_M1"]  # variação anual e variação mensal

# Paleta do relatório: branco e azul-marinho, com tons de apoio
NAVY = "#0B1F3A"
BLUE = "#1F4E8C"
LIGHT_BLUE = "#8FB0D9"
GREY = "#6B7785"
GRID = "#E6EAF0"


def get_eurostat_data(code, geo=geo_code, unit=unit_code):
    """
    Busca um dataset na Eurostat a partir do nome da categoria no dicionário
    hicp_categories (ex.: "HICP - energy"). Retorna None se algo der errado.
    """
    try:
        return eurostat.get_data_df(
            hicp_categories[code], filter_pars={"geo": geo, "unit": unit}
        )
    except Exception as e:
        print(f"Erro ao buscar '{code}' na Eurostat: {e}")
        return None


def tidy(df, category):
    """
    A Eurostat devolve os dados em formato largo (um mês por coluna).
    Aqui viramos isso para o formato longo, que é o que o plotly prefere.
    """
    period_cols = [c for c in df.columns if c[:2] == "20"]
    long = df.melt(
        id_vars=["unit"], value_vars=period_cols, var_name="period", value_name="value"
    )
    long["period"] = pd.to_datetime(long["period"])
    long["category"] = category
    return long.dropna(subset=["value"])


def load_all():
    """
    Percorre o dicionário inteiro e junta tudo em um único DataFrame longo.
    Categorias que falharem são só ignoradas, para não derrubar o relatório.
    """
    frames = []
    for name in hicp_categories:
        raw = get_eurostat_data(name)
        if raw is not None and not raw.empty:
            frames.append(tidy(raw, name.replace("HICP - ", "").capitalize()))
    return pd.concat(frames, ignore_index=True)


def base_layout(fig, title, height=450):
    """Aplica o visual padrão (fundo branco, tipografia sóbria) aos gráficos."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=NAVY), x=0),
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Helvetica, Arial, sans-serif", color=NAVY, size=12),
        height=height,
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", y=-0.15),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=GREY)
    fig.update_yaxes(gridcolor=GRID, linecolor=GREY)
    return fig


def line_chart(data, title):
    """Série da inflação anual (linha) e mensal (barras) do índice geral."""
    annual = data[data["unit"] == "PCH_M12"]
    monthly = data[data["unit"] == "PCH_M1"]
    fig = go.Figure()
    fig.add_bar(
        x=monthly["period"], y=monthly["value"], name="Variação mensal (%)",
        marker_color=LIGHT_BLUE,
    )
    fig.add_scatter(
        x=annual["period"], y=annual["value"], name="Variação anual (%)",
        mode="lines+markers", line=dict(color=NAVY, width=3),
    )
    fig.update_yaxes(ticksuffix="%")
    return base_layout(fig, title)


def category_bar(latest, title):
    """Barras horizontais com a inflação anual mais recente por categoria."""
    latest = latest.sort_values("value")
    fig = go.Figure(
        go.Bar(
            x=latest["value"], y=latest["category"], orientation="h",
            marker_color=[NAVY if v >= 0 else LIGHT_BLUE for v in latest["value"]],
            text=latest["value"].map("{:.1f}%".format), textposition="outside",
        )
    )
    fig.update_xaxes(ticksuffix="%")
    return base_layout(fig, title, height=700)


def heatmap(pivot, title):
    """Mapa de calor: categorias nas linhas, meses nas colunas."""
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values, x=[d.strftime("%b/%y") for d in pivot.columns],
            y=pivot.index, colorscale=[[0, "#FFFFFF"], [1, NAVY]],
            colorbar=dict(title="%"),
            hovertemplate="%{y}<br>%{x}: %{z:.1f}%<extra></extra>",
        )
    )
    return base_layout(fig, title, height=700)


# ---------------------------------------------------------------------------
# Tradução dos nomes das categorias (os dados chegam em inglês)
# ---------------------------------------------------------------------------
PT_NAMES = {
    "All items": "Índice geral",
    "Food": "Alimentos",
    "Alcohol and tobacco": "Álcool e tabaco",
    "Clothing": "Vestuário",
    "Housing": "Habitação",
    "Household equipment": "Equipamento doméstico",
    "Health": "Saúde",
    "Transport": "Transporte",
    "Communications": "Comunicações",
    "Recreation and culture": "Lazer e cultura",
    "Education": "Educação",
    "Hotels and restaurants": "Hotéis e restaurantes",
    "Miscellaneous goods and services": "Bens e serviços diversos",
    "Services": "Serviços",
    "Energy": "Energia",
    "Non-energy industrial goods": "Bens industriais (ex-energia)",
    "Food, alcohol and tobacco": "Alimentos, álcool e tabaco",
    "All items excluding energy, food, alcohol and tobacco": "Núcleo",
}


def pt(name):
    return PT_NAMES.get(name, name)


# ---------------------------------------------------------------------------
# Incidência: quanto cada grupo contribui, em pontos percentuais, para a
# inflação anual (peso do grupo na cesta x variação anual do grupo)
# ---------------------------------------------------------------------------
# Os pesos vêm do dataset prc_hicp_inw (por mil). Ele ainda não tem EA21,
# então usamos a zona do euro com 20 países e o ano mais recente.
WEIGHT_GEO = "EA20"

# Quatro grupos que, somados, fecham exatamente a cesta (peso total = 1000)
MAIN_GROUPS = {
    "Food, alcohol and tobacco": "FOOD",
    "Energy": "NRG",
    "Non-energy industrial goods": "IGD_NNRG",
    "Services": "SERV",
}

# Divisões da cesta (COICOP) para o detalhe por categoria
DIVISIONS = {
    "Food": "CP01", "Alcohol and tobacco": "CP02", "Clothing": "CP03",
    "Housing": "CP04", "Household equipment": "CP05", "Health": "CP06",
    "Transport": "CP07", "Communications": "CP08",
    "Recreation and culture": "CP09", "Education": "CP10",
    "Hotels and restaurants": "CP11",
}


def get_weights():
    """Pesos mais recentes de cada item na cesta, já em fração (soma = 1)."""
    raw = eurostat.get_data_df(
        "prc_hicp_inw", filter_pars={"geo": WEIGHT_GEO, "startPeriod": 2024}
    )
    year = max(c for c in raw.columns if c.isdigit())
    return (raw.set_index("coicop")[year] / 1000), year


def contributions(annual, weights, mapping):
    """Contribuição (p.p.) de cada grupo em cada mês."""
    out = []
    for cat, code in mapping.items():
        s = annual[annual["category"] == cat][["period", "value"]].copy()
        s["contribution"] = s["value"] * weights[code]
        s["category"] = cat
        out.append(s)
    return pd.concat(out)


def incidence_chart(contrib, headline, title):
    """Barras empilhadas: o que cada grupo adiciona à inflação anual."""
    colors = {
        "Food, alcohol and tobacco": NAVY,
        "Energy": BLUE,
        "Non-energy industrial goods": LIGHT_BLUE,
        "Services": GREY,
    }
    fig = go.Figure()
    for cat, color in colors.items():
        s = contrib[contrib["category"] == cat]
        fig.add_bar(x=s["period"], y=s["contribution"], name=pt(cat),
                    marker_color=color)
    fig.add_scatter(x=headline["period"], y=headline["value"],
                    name="Inflação anual", mode="lines+markers",
                    line=dict(color="#C0392B", width=2, dash="dot"))
    fig.update_layout(barmode="relative")
    fig.update_yaxes(ticksuffix=" p.p.", zeroline=True, zerolinecolor=NAVY)
    fig.update_xaxes(tickformat="%b/%y")
    return base_layout(fig, title, height=480)


def division_incidence_chart(contrib_latest, title):
    """Contribuição de cada divisão da cesta no último mês, em p.p."""
    d = contrib_latest.sort_values("contribution")
    fig = go.Figure(
        go.Bar(
            x=d["contribution"], y=[pt(c) for c in d["category"]],
            orientation="h",
            marker_color=[NAVY if v >= 0 else LIGHT_BLUE for v in d["contribution"]],
            text=d["contribution"].map("{:+.2f}".format),
            textposition="outside", cliponaxis=False,
        )
    )
    fig.update_xaxes(ticksuffix=" p.p.")
    fig.update_yaxes(automargin=True)
    fig.update_layout(margin=dict(l=10, r=50, t=60, b=10), showlegend=False)
    return base_layout(fig, title, height=520)


def heatmap_pt(pivot, title):
    """Mapa de calor com valores escritos nas células e rótulos em português."""
    labels = [pt(c) for c in pivot.index]
    months = [d.strftime("%b/%y") for d in pivot.columns]
    vmax = float(pivot.abs().max().max())
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values, x=months, y=labels,
            zmin=-vmax, zmax=vmax, zmid=0,
            colorscale=[[0, LIGHT_BLUE], [0.5, "#FFFFFF"], [1, NAVY]],
            xgap=2, ygap=2,
            text=pivot.round(1).astype(str).values, texttemplate="%{text}",
            textfont=dict(size=10),
            colorbar=dict(title="%", thickness=12),
            hovertemplate="%{y}<br>%{x}: %{z:.1f}%<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed", automargin=True)
    fig.update_xaxes(side="top", tickangle=0)
    return base_layout(fig, title, height=60 + 38 * len(labels))
