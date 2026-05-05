# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from src.dados_tesouro import dados_tesouro


# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Dashboard Tesouro Direto",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================
# PALETA
# =========================
COR_PRIMARIA = "#0F46AB"
COR_FUNDO = "#FFFFFF"
COR_TEXTO = "#10243E"
COR_TEXTO_SUAVE = "#6B7A90"
COR_SUPERFICIE = "#FFFFFF"
COR_BORDA = "#D9E2EF"

PALETA_GRAFICOS = [
    "#0F46AB",
    "#3A6FD8",
    "#5A8BEB",
    "#7BA5F3",
    "#9CBDF7",
    "#BDD3FA",
    "#E6E6E6",
]


# =========================
# ESTILO
# =========================
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {COR_FUNDO};
            color: {COR_TEXTO};
        }}

        .block-container {{
            padding-top: 1.15rem;
            padding-bottom: 1.5rem;
            max-width: 110rem;
        }}

        .kpi-card {{
            background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
            border: 1px solid {COR_BORDA};
            padding: 10px 12px;
            border-radius: 16px;
            box-shadow: 0 14px 32px rgba(15,70,171,0.06);
            margin-bottom: 0.4rem;
        }}

        .kpi-title {{
            font-size: 0.74rem;
            color: {COR_TEXTO_SUAVE};
            margin-bottom: 3px;
            line-height: 1.05;
        }}

        .kpi-value {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {COR_TEXTO};
            line-height: 1.05;
        }}

        .kpi-sub {{
            font-size: 0.68rem;
            color: {COR_TEXTO_SUAVE};
            margin-top: 2px;
            line-height: 1.0;
        }}

        .section-title {{
            font-size: 0.96rem;
            font-weight: 600;
            margin-top: 0.1rem;
            margin-bottom: 0.55rem;
            color: {COR_TEXTO};
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid {COR_BORDA};
            border-radius: 16px;
            background-color: #fbfcfe;
        }}

        div[data-testid="stSidebar"] {{
            background-color: #f7f9fc;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {COR_BORDA};
            border-radius: 14px;
            overflow: hidden;
        }}

        .stDownloadButton > button {{
            background-color: {COR_PRIMARIA};
            color: white;
            border: none;
            border-radius: 10px;
        }}

        .stDownloadButton > button:hover {{
            background-color: #0c3b90;
            color: white;
        }}

        div[data-testid="stDateInput"] input,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
            background-color: #ffffff;
            border: 1px solid {COR_BORDA};
            color: {COR_TEXTO};
            border-radius: 14px;
        }}

        div[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
            background: {COR_PRIMARIA} !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        div[data-testid="stMultiSelect"] [data-baseweb="tag"] span {{
            color: #FFFFFF !important;
        }}

        div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {{
            fill: #FFFFFF !important;
        }}

        h1, h2, h3, p, label, span {{
            color: {COR_TEXTO};
        }}
    </style>
""",
    unsafe_allow_html=True,
)


# =========================
# FUNÇÕES AUXILIARES
# =========================
URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/"
    "precotaxatesourodireto.csv"
)
BASE_DIR = Path(__file__).resolve().parent
TESOURO_SNAPSHOT_PATH = BASE_DIR / "data" / "tesouro_direto_snapshot.pkl"
TESOURO_SNAPSHOT_CSV_PATH = BASE_DIR / "data" / "tesouro_direto_snapshot.csv.gz"


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    if TESOURO_SNAPSHOT_CSV_PATH.exists():
        df = pd.read_csv(TESOURO_SNAPSHOT_CSV_PATH, compression="gzip", parse_dates=["Data Vencimento", "Data Base"])
    elif TESOURO_SNAPSHOT_PATH.exists():
        df = pd.read_pickle(TESOURO_SNAPSHOT_PATH)
    else:
        df = dados_tesouro(URL)
    return df.sort_values("Data Base").copy()


def formatar_numero(valor: float, casas: int = 2) -> str:
    if pd.isna(valor):
        return "-"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def criar_nome_serie(df_base: pd.DataFrame) -> pd.DataFrame:
    df_base = df_base.copy()
    df_base["Nome Serie"] = (
        df_base["Tipo Titulo"].astype(str)
        + " • "
        + df_base["Data Vencimento"].dt.strftime("%d/%m/%Y")
    )
    return df_base


def resumo_metrica(df_base: pd.DataFrame, metrica: str):
    base = df_base.sort_values("Data Base").copy()
    if base.empty or metrica not in base.columns:
        return pd.NA, pd.NA, pd.NA
    base = base.dropna(subset=[metrica])
    if base.empty:
        return pd.NA, pd.NA, pd.NA
    valor_atual = base[metrica].iloc[-1]
    valor_min = base[metrica].min()
    valor_max = base[metrica].max()
    return valor_atual, valor_min, valor_max


def formatar_data_segura(valor) -> str:
    data = pd.to_datetime(valor, errors="coerce")
    if pd.isna(data):
        return "-"
    return data.strftime("%d/%m/%Y")


def adicionar_marcacoes_extremos(fig, df_plot: pd.DataFrame, metrica: str):
    """
    Mostra rótulos Mín / Máx / Atual apenas quando houver
    menos de 3 séries no gráfico (até 2 linhas).
    """
    series_unicas = list(df_plot["Nome Serie"].unique())
    if len(series_unicas) >= 3:
        return fig

    for serie in series_unicas:
        base_serie = (
            df_plot[df_plot["Nome Serie"] == serie]
            .sort_values("Data Base")
            .copy()
        )
        if base_serie.empty:
            continue

        ponto_atual = base_serie.iloc[-1]
        ponto_min = base_serie.loc[base_serie[metrica].idxmin()]
        ponto_max = base_serie.loc[base_serie[metrica].idxmax()]

        fig.add_trace(
            go.Scatter(
                x=[ponto_min["Data Base"]],
                y=[ponto_min[metrica]],
                mode="markers+text",
                text=["Mín"],
                textposition="bottom center",
                marker=dict(size=7, symbol="diamond", color=COR_TEXTO),
                showlegend=False,
                hovertemplate=(
                    f"{serie}<br>"
                    f"Data: {ponto_min['Data Base'].strftime('%d/%m/%Y')}<br>"
                    f"{metrica}: {ponto_min[metrica]:.2f}<br>"
                    "Marcador: Mín<extra></extra>"
                ),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ponto_max["Data Base"]],
                y=[ponto_max[metrica]],
                mode="markers+text",
                text=["Máx"],
                textposition="top center",
                marker=dict(size=7, symbol="diamond", color=COR_TEXTO),
                showlegend=False,
                hovertemplate=(
                    f"{serie}<br>"
                    f"Data: {ponto_max['Data Base'].strftime('%d/%m/%Y')}<br>"
                    f"{metrica}: {ponto_max[metrica]:.2f}<br>"
                    "Marcador: Máx<extra></extra>"
                ),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ponto_atual["Data Base"]],
                y=[ponto_atual[metrica]],
                mode="markers+text",
                text=["Atual"],
                textposition="middle right",
                marker=dict(size=8, symbol="circle", color=COR_PRIMARIA),
                showlegend=False,
                hovertemplate=(
                    f"{serie}<br>"
                    f"Data: {ponto_atual['Data Base'].strftime('%d/%m/%Y')}<br>"
                    f"{metrica}: {ponto_atual[metrica]:.2f}<br>"
                    "Marcador: Atual<extra></extra>"
                ),
            )
        )

    return fig


def estilizar_layout_plotly(fig, titulo_legenda: str, altura: int = 780):
    """
    Legenda horizontal no topo, com espaço para não colidir com o título.
    """
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor="#FCFDFF",
        font=dict(color=COR_TEXTO, size=13),
        title=dict(
            x=0,
            xanchor="left",
            y=0.985,
            yanchor="top",
            font=dict(size=18, color=COR_TEXTO),
        ),
        legend=dict(
            title=dict(
                text=titulo_legenda,
                font=dict(size=12, color=COR_TEXTO),
            ),
            font=dict(size=10, color=COR_TEXTO),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="rgba(16,36,62,0.10)",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            itemclick="toggleothers",
            itemdoubleclick="toggle",
        ),
        height=altura,
        margin=dict(l=10, r=10, t=140, b=10),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(16,36,62,0.08)",
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(16,36,62,0.08)",
        zeroline=False,
    )
    return fig


# =========================
# APP
# =========================
df = carregar_dados()

st.title("Títulos Públicos")

tipos_disponiveis = sorted(df["Tipo Titulo"].dropna().unique())
data_min = df["Data Base"].min().date()
data_max = df["Data Base"].max().date()

col_f1, col_f2, col_f3, col_f4 = st.columns([2.4, 1.05, 1.05, 1.15])

with col_f1:
    titulos_selecionados = st.multiselect(
        "Títulos",
        options=tipos_disponiveis,
        default=[],
        placeholder="Selecione os títulos",
    )

with col_f2:
    data_inicio = st.date_input(
        "Início",
        value=data_min,
        min_value=data_min,
        max_value=data_max,
    )

with col_f3:
    data_fim = st.date_input(
        "Fim",
        value=data_max,
        min_value=data_min,
        max_value=data_max,
    )

with col_f4:
    coluna_valor = st.selectbox(
        "Métrica",
        options=[
            "Taxa Compra Manha",
            "Taxa Venda Manha",
            "PU Compra Manha",
            "PU Venda Manha",
            "PU Base Manha",
        ],
        index=0,
    )

if data_inicio > data_fim:
    st.warning("A data inicial não pode ser maior que a data final.")
    st.stop()

if not titulos_selecionados:
    st.info("Selecione ao menos um título para visualizar os dados.")
    st.stop()

df_filtrado = df[
    (df["Tipo Titulo"].isin(titulos_selecionados))
    & (df["Data Base"].dt.date >= data_inicio)
    & (df["Data Base"].dt.date <= data_fim)
].copy()

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

hoje = pd.Timestamp.today().normalize()

with st.expander("Refinar vencimentos", expanded=True):
    incluir_vencidos = st.checkbox("Incluir títulos com vencimento passado", value=False)

    vencimentos_ativos = sorted(
        df_filtrado.loc[df_filtrado["Data Vencimento"] >= hoje, "Data Vencimento"]
        .dropna()
        .unique()
    )

    vencimentos_vencidos = sorted(
        df_filtrado.loc[df_filtrado["Data Vencimento"] < hoje, "Data Vencimento"]
        .dropna()
        .unique()
    )

    opcoes_vencimento = (
        vencimentos_ativos
        + [v for v in vencimentos_vencidos if v not in vencimentos_ativos]
        if incluir_vencidos
        else vencimentos_ativos
    )

    default_vencimentos = vencimentos_ativos.copy()

    vencimentos_selecionados = st.multiselect(
        "Vencimentos",
        options=opcoes_vencimento,
        default=default_vencimentos,
        format_func=lambda x: x.strftime("%d/%m/%Y"),
    )

    if vencimentos_selecionados:
        df_filtrado = df_filtrado[df_filtrado["Data Vencimento"].isin(vencimentos_selecionados)]
    else:
        df_filtrado = df_filtrado.iloc[0:0]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado após o refinamento por vencimento.")
    st.stop()

df_filtrado = criar_nome_serie(df_filtrado)

ultima_data = df_filtrado["Data Base"].max()
df_ultima_data = df_filtrado[df_filtrado["Data Base"] == ultima_data].copy()

taxa_media = df_ultima_data["Taxa Compra Manha"].mean()
pu_medio = df_ultima_data["PU Compra Manha"].mean()

serie_plot = (
    df_filtrado.groupby(["Data Base", "Nome Serie"], as_index=False)[coluna_valor].mean()
)

serie_global = (
    serie_plot.groupby("Data Base", as_index=False)[coluna_valor]
    .mean()
    .sort_values("Data Base")
)

if serie_global.empty or serie_global[coluna_valor].dropna().empty:
    st.warning("Nenhum dado válido encontrado para a métrica e intervalo selecionados.")
    st.stop()

valor_atual, valor_min, valor_max = resumo_metrica(serie_global, coluna_valor)

col_principal, col_kpis = st.columns([4.2, 0.9])

with col_principal:
    fig_linha = px.line(
        serie_plot,
        x="Data Base",
        y=coluna_valor,
        color="Nome Serie",
        color_discrete_sequence=PALETA_GRAFICOS,
        title=f"Evolução de {coluna_valor}",
        render_mode="svg",
    )

    fig_linha = adicionar_marcacoes_extremos(fig_linha, serie_plot, coluna_valor)

    fig_linha.update_layout(
        xaxis_title="Data Base",
        yaxis_title=coluna_valor,
        hovermode="x unified",
    )

    fig_linha = estilizar_layout_plotly(fig_linha, "Título • Vencimento", altura=820)
    st.plotly_chart(fig_linha, width="stretch")

with col_kpis:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Taxa</div>
            <div class="kpi-value">{formatar_numero(taxa_media)}%</div>
            <div class="kpi-sub">últ. base</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">PU</div>
            <div class="kpi-value">R$ {formatar_numero(pu_medio)}</div>
            <div class="kpi-sub">{formatar_data_segura(ultima_data)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Atual</div>
            <div class="kpi-value">{formatar_numero(valor_atual)}</div>
            <div class="kpi-sub">{coluna_valor}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Mín</div>
            <div class="kpi-value">{formatar_numero(valor_min)}</div>
            <div class="kpi-sub">{coluna_valor}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Máx</div>
            <div class="kpi-value">{formatar_numero(valor_max)}</div>
            <div class="kpi-sub">{coluna_valor}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-title">Tabela detalhada</div>', unsafe_allow_html=True)

mostrar_detalhes = st.checkbox("Mostrar colunas adicionais", value=False)

tabela = df_filtrado.copy()
tabela["Data Base"] = tabela["Data Base"].dt.strftime("%d/%m/%Y")
tabela["Data Vencimento"] = tabela["Data Vencimento"].dt.strftime("%d/%m/%Y")

colunas_principais = [
    "Tipo Titulo",
    "Data Vencimento",
    "Data Base",
    "Taxa Compra Manha",
    "PU Compra Manha",
]

colunas_adicionais = [
    "Nome Serie",
    "Taxa Venda Manha",
    "PU Venda Manha",
    "PU Base Manha",
]

colunas_exibidas = colunas_principais + colunas_adicionais if mostrar_detalhes else colunas_principais

st.dataframe(
    tabela[colunas_exibidas],
    use_container_width=True,
    hide_index=True,
)

csv = df_filtrado.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")

st.download_button(
    label="Baixar dados filtrados em CSV",
    data=csv,
    file_name="dados_tesouro_filtrados.csv",
    mime="text/csv",
)
