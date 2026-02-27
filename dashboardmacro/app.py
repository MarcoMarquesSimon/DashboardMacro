# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dados_tesouro import dados_tesouro


# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Dashboard Tesouro Direto",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# PALETA
# =========================
COR_PRIMARIA = "#0F46AB"
COR_FUNDO = "#061630"
COR_TEXTO = "#E6E6E6"
COR_SUPERFICIE = "#2B2B2B"

PALETA_GRAFICOS = [
    "#0F46AB",
    "#3A6FD8",
    "#5A8BEB",
    "#7BA5F3",
    "#9CBDF7",
    "#BDD3FA",
    "#E6E6E6"
]


# =========================
# ESTILO
# =========================
st.markdown(f"""
    <style>
        .stApp {{
            background-color: {COR_FUNDO};
            color: {COR_TEXTO};
        }}

        .block-container {{
            padding-top: 1.15rem;
            padding-bottom: 1.5rem;
            max-width: 95rem;
        }}

        .kpi-card {{
            background: {COR_SUPERFICIE};
            border: 1px solid rgba(230,230,230,0.07);
            padding: 10px 12px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.12);
            margin-bottom: 0.4rem;
        }}

        .kpi-title {{
            font-size: 0.74rem;
            color: rgba(230,230,230,0.78);
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
            color: rgba(230,230,230,0.54);
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
            border: 1px solid rgba(230,230,230,0.07);
            border-radius: 14px;
            background-color: rgba(43,43,43,0.25);
        }}

        div[data-testid="stSidebar"] {{
            background-color: {COR_SUPERFICIE};
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid rgba(230,230,230,0.06);
            border-radius: 12px;
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

        h1, h2, h3, p, label, span {{
            color: {COR_TEXTO};
        }}
    </style>
""", unsafe_allow_html=True)


# =========================
# FUNÇÕES AUXILIARES
# =========================
URL = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"


@st.cache_data
def carregar_dados():
    df = dados_tesouro(URL)
    return df.sort_values("Data Base").copy()


def formatar_numero(valor, casas=2):
    if pd.isna(valor):
        return "-"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def criar_nome_serie(df_base):
    df_base = df_base.copy()
    df_base["Nome Serie"] = (
        df_base["Tipo Titulo"].astype(str)
        + " • "
        + df_base["Data Vencimento"].dt.strftime("%d/%m/%Y")
    )
    return df_base


def resumo_metrica(df_base, metrica):
    base = df_base.sort_values("Data Base").copy()
    valor_atual = base[metrica].iloc[-1]
    valor_min = base[metrica].min()
    valor_max = base[metrica].max()
    return valor_atual, valor_min, valor_max


def adicionar_marcacoes_extremos(fig, df_plot, metrica):
    """
    Até 6 séries: mostra Mín, Máx e Atual
    Acima de 6 séries: mostra só Atual
    """
    series_unicas = list(df_plot["Nome Serie"].unique())
    mostrar_extremos_completos = len(series_unicas) <= 6

    for serie in series_unicas:
        base_serie = (
            df_plot[df_plot["Nome Serie"] == serie]
            .sort_values("Data Base")
            .copy()
        )

        if base_serie.empty:
            continue

        ponto_atual = base_serie.iloc[-1]

        if mostrar_extremos_completos:
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
                    name=f"{serie} - Mín",
                    showlegend=False,
                    hovertemplate=(
                        f"{serie}<br>"
                        f"Data: {ponto_min['Data Base'].strftime('%d/%m/%Y')}<br>"
                        f"{metrica}: {ponto_min[metrica]:.2f}<br>"
                        "Marcador: Mín<extra></extra>"
                    )
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
                    name=f"{serie} - Máx",
                    showlegend=False,
                    hovertemplate=(
                        f"{serie}<br>"
                        f"Data: {ponto_max['Data Base'].strftime('%d/%m/%Y')}<br>"
                        f"{metrica}: {ponto_max[metrica]:.2f}<br>"
                        "Marcador: Máx<extra></extra>"
                    )
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
                name=f"{serie} - Atual",
                showlegend=False,
                hovertemplate=(
                    f"{serie}<br>"
                    f"Data: {ponto_atual['Data Base'].strftime('%d/%m/%Y')}<br>"
                    f"{metrica}: {ponto_atual[metrica]:.2f}<br>"
                    "Marcador: Atual<extra></extra>"
                )
            )
        )

    return fig


def estilizar_layout_plotly(fig, titulo_legenda, altura=780):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor=COR_FUNDO,
        font=dict(color=COR_TEXTO, size=13),
        legend=dict(
            title=dict(
                text=titulo_legenda,
                font=dict(size=12, color=COR_TEXTO)
            ),
            font=dict(size=10, color=COR_TEXTO),
            bgcolor="rgba(43,43,43,0.55)",
            bordercolor="rgba(230,230,230,0.08)",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            itemclick="toggleothers",
            itemdoubleclick="toggle"
        ),
        height=altura,
        margin=dict(l=10, r=10, t=95, b=10)
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(230,230,230,0.08)",
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(230,230,230,0.08)",
        zeroline=False
    )

    return fig


# =========================
# CARGA DOS DADOS
# =========================
df = carregar_dados()


# =========================
# SIDEBAR - NAVEGAÇÃO
# =========================
st.sidebar.title("Painéis")
pagina = st.sidebar.radio(
    "Selecione o dashboard",
    options=["Tesouro Direto", "Análise Macro"],
    label_visibility="collapsed"
)


# =========================
# PÁGINA 1 - TESOURO DIRETO
# =========================
if pagina == "Tesouro Direto":

    st.title("Títulos Públicos")

    tipos_disponiveis = sorted(df["Tipo Titulo"].dropna().unique())
    data_min = df["Data Base"].min().date()
    data_max = df["Data Base"].max().date()

    col_f1, col_f2, col_f3, col_f4 = st.columns([2.4, 1.05, 1.05, 1.15])

    with col_f1:
        titulos_selecionados = st.multiselect(
            "Títulos",
            options=tipos_disponiveis,
            default=tipos_disponiveis[:2] if len(tipos_disponiveis) >= 2 else tipos_disponiveis,
            placeholder="Selecione os títulos"
        )

    with col_f2:
        data_inicio = st.date_input(
            "Início",
            value=data_min,
            min_value=data_min,
            max_value=data_max
        )

    with col_f3:
        data_fim = st.date_input(
            "Fim",
            value=data_max,
            min_value=data_min,
            max_value=data_max
        )

    with col_f4:
        coluna_valor = st.selectbox(
            "Métrica",
            options=[
                "Taxa Compra Manha",
                "Taxa Venda Manha",
                "PU Compra Manha",
                "PU Venda Manha",
                "PU Base Manha"
            ],
            index=0
        )

    if data_inicio > data_fim:
        st.warning("A data inicial não pode ser maior que a data final.")
        st.stop()

    if not titulos_selecionados:
        st.warning("Selecione ao menos um título.")
        st.stop()

    df_filtrado = df[
        (df["Tipo Titulo"].isin(titulos_selecionados)) &
        (df["Data Base"].dt.date >= data_inicio) &
        (df["Data Base"].dt.date <= data_fim)
    ].copy()

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
        st.stop()

    hoje = pd.Timestamp.today().normalize()

    with st.expander("Refinar vencimentos", expanded=False):
        incluir_vencidos = st.checkbox(
            "Incluir títulos com vencimento passado",
            value=False
        )

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

        if incluir_vencidos:
            opcoes_vencimento = vencimentos_ativos + [
                v for v in vencimentos_vencidos if v not in vencimentos_ativos
            ]
        else:
            opcoes_vencimento = vencimentos_ativos

        default_vencimentos = vencimentos_ativos.copy()

        vencimentos_selecionados = st.multiselect(
            "Vencimentos",
            options=opcoes_vencimento,
            default=default_vencimentos,
            format_func=lambda x: x.strftime("%d/%m/%Y")
        )

        if vencimentos_selecionados:
            df_filtrado = df_filtrado[
                df_filtrado["Data Vencimento"].isin(vencimentos_selecionados)
            ]
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
        df_filtrado
        .groupby(["Data Base", "Nome Serie"], as_index=False)[coluna_valor]
        .mean()
    )

    serie_global = (
        serie_plot
        .groupby("Data Base", as_index=False)[coluna_valor]
        .mean()
        .sort_values("Data Base")
    )

    valor_atual, valor_min, valor_max = resumo_metrica(serie_global, coluna_valor)

    col_principal, col_kpis = st.columns([4.2, 0.9])

    with col_principal:
        fig_linha = px.line(
            serie_plot,
            x="Data Base",
            y=coluna_valor,
            color="Nome Serie",
            color_discrete_sequence=PALETA_GRAFICOS,
            title=f"Evolução de {coluna_valor}"
        )

        fig_linha = adicionar_marcacoes_extremos(fig_linha, serie_plot, coluna_valor)

        fig_linha.update_layout(
            xaxis_title="Data Base",
            yaxis_title=coluna_valor,
            hovermode="x unified"
        )

        fig_linha = estilizar_layout_plotly(
            fig_linha,
            "Título • Vencimento",
            altura=780
        )

        st.plotly_chart(fig_linha, use_container_width=True)

    with col_kpis:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Taxa</div>
                <div class="kpi-value">{formatar_numero(taxa_media)}%</div>
                <div class="kpi-sub">últ. base</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">PU</div>
                <div class="kpi-value">R$ {formatar_numero(pu_medio)}</div>
                <div class="kpi-sub">{ultima_data.strftime("%d/%m/%Y")}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Atual</div>
                <div class="kpi-value">{formatar_numero(valor_atual)}</div>
                <div class="kpi-sub">{coluna_valor}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Mín</div>
                <div class="kpi-value">{formatar_numero(valor_min)}</div>
                <div class="kpi-sub">{coluna_valor}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Máx</div>
                <div class="kpi-value">{formatar_numero(valor_max)}</div>
                <div class="kpi-sub">{coluna_valor}</div>
            </div>
        """, unsafe_allow_html=True)

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
        "PU Compra Manha"
    ]

    colunas_adicionais = [
        "Nome Serie",
        "Taxa Venda Manha",
        "PU Venda Manha",
        "PU Base Manha"
    ]

    colunas_exibidas = colunas_principais + colunas_adicionais if mostrar_detalhes else colunas_principais

    st.dataframe(
        tabela[colunas_exibidas],
        use_container_width=True,
        hide_index=True
    )

    csv = df_filtrado.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")

    st.download_button(
        label="Baixar dados filtrados em CSV",
        data=csv,
        file_name="dados_tesouro_filtrados.csv",
        mime="text/csv"
    )


# =========================
# PÁGINA 2 - ANÁLISE MACRO
# =========================
elif pagina == "Análise Macro":
    st.title("Dashboard de Análise Macro")
    st.caption("Página reservada para a próxima etapa do projeto.")
    st.info("Em breve: este painel receberá indicadores macroeconômicos, curvas e comparações.")
