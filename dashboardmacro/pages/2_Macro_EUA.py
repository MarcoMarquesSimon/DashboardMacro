# -*- coding: utf-8 -*-
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dados_fred import fetch_all_fred_indicators, fetch_series_variant


st.set_page_config(page_title="Painel Macro EUA", page_icon="📊", layout="wide")


COR_PRIMARIA = "#0F46AB"
COR_FUNDO = "#FFFFFF"
COR_TEXTO = "#10243E"
COR_TEXTO_SUAVE = "#6B7A90"
COR_BORDA = "#D9E2EF"
COR_POSITIVA = "#2DBE60"
COR_NEGATIVA = "#E04F5F"
COR_INFO = "#EAF2FF"
COR_INFO_BORDA = "#C9DAF8"
CASAS = 2
BASE_DIR = Path(__file__).resolve().parents[1]
SNAPSHOT_US_PATH = BASE_DIR / "data" / "macro_eua_snapshot.pkl"
SNAPSHOT_US_CSV_PATH = BASE_DIR / "data" / "macro_eua_snapshot.csv.gz"
DATA_PIPELINE_VERSION = "2026-04-15-v1"
DEFAULT_FRED_API_KEY = "da9de0f64ae8f49db8bfc2b01d51c163"

PERIOD_OPTIONS = ["6M", "1Y", "3Y", "5Y", "10Y", "YTD", "Tudo"]
FREQ_OPTIONS_US = ["Todas", "Mensal", "Trimestral", "Diária", "Semanal", "Quinzenal", "Anual"]
FREQ_LABEL_TO_FRED = {
    "Mensal": "m",
    "Trimestral": "q",
    "Diária": "d",
    "Semanal": "w",
    "Quinzenal": "bw",
    "Anual": "a",
}

INFLATION_FREQ_VARIANTS = {
    "cpi": {
        "Mensal": {"series_id": "CPIAUCSL", "frequency": "m"},
        "Trimestral": {"series_id": "CPIAUCSL", "frequency": "q"},
    },
    "ppi": {
        "Mensal": {"series_id": "PCUOMFGOMFG", "frequency": "m"},
        "Trimestral": {"series_id": "PCUOMFGOMFG", "frequency": "q"},
    },
    "core_pce": {
        "Mensal": {"series_id": "PCEPILFE", "frequency": "m"},
        "Trimestral": {"series_id": "DPCCRV1Q225SBEA", "frequency": "q"},
    },
}


st.markdown(
    f"""
    <style>
        .stApp {{
            background: {COR_FUNDO};
            color: {COR_TEXTO};
        }}

        .block-container {{
            max-width: 120rem;
            padding-top: 3.05rem;
            padding-bottom: 2rem;
        }}

        h1, h2, h3, label, p, span {{
            color: {COR_TEXTO};
        }}

        .macro-top {{
            margin-top: 0.25rem;
            margin-bottom: 1.25rem;
        }}

        .macro-title {{
            font-size: 2.15rem;
            line-height: 1.12;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.35rem;
            color: {COR_TEXTO};
        }}

        .macro-subtitle {{
            color: {COR_TEXTO_SUAVE};
            font-size: 1rem;
            margin-bottom: 0;
        }}

        .range-note {{
            color: {COR_TEXTO_SUAVE};
            font-size: 0.95rem;
            margin: 0.3rem 0 1rem 0;
        }}

        .chart-head {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: flex-start;
            margin-bottom: 0.55rem;
        }}

        .chart-title {{
            font-size: 1.1rem;
            font-weight: 800;
            line-height: 1.2;
            color: {COR_TEXTO};
            margin: 0 0 0.25rem 0;
        }}

        .chart-subtitle {{
            color: {COR_TEXTO_SUAVE};
            font-size: 0.88rem;
            line-height: 1.35;
            margin: 0;
        }}

        .metric-wrap {{
            min-width: 280px;
            text-align: right;
        }}

        .metric-label {{
            color: {COR_TEXTO_SUAVE};
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 0 0 0.18rem 0;
        }}

        .metric-value {{
            font-size: 2.15rem;
            font-weight: 800;
            line-height: 1;
            color: {COR_TEXTO};
            margin: 0 0 0.28rem 0;
            letter-spacing: -0.04em;
        }}

        .metric-date {{
            color: {COR_TEXTO_SUAVE};
            font-size: 0.86rem;
            margin: 0 0 0.38rem 0;
        }}

        .metric-pills {{
            display: flex;
            justify-content: flex-end;
            gap: 0.45rem;
            flex-wrap: wrap;
        }}

        .metric-pill {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.34rem 0.7rem;
            font-size: 0.8rem;
            font-weight: 700;
            line-height: 1;
        }}

        .metric-pos {{
            background: rgba(45, 190, 96, 0.12);
            color: #127A3D;
        }}

        .metric-neg {{
            background: rgba(224, 79, 95, 0.12);
            color: #B53A49;
        }}

        .metric-neutral {{
            background: rgba(15, 70, 171, 0.08);
            color: {COR_PRIMARIA};
        }}

        .inline-alert {{
            background: {COR_INFO};
            border: 1px solid {COR_INFO_BORDA};
            color: {COR_PRIMARIA};
            border-radius: 16px;
            padding: 0.8rem 0.95rem;
            font-size: 0.92rem;
            margin-bottom: 0.8rem;
        }}

        .filter-label {{
            font-size: 0.95rem;
            font-weight: 500;
            color: {COR_TEXTO};
            margin: 0 0 0.35rem 0;
        }}

        .filter-action {{
            margin-top: 1.55rem;
        }}

        .filter-row-bottom {{
            padding-top: 0.15rem;
        }}

        .range-radio-wrap {{
            padding-top: 0.1rem;
        }}

        div[data-testid="stPopover"] > button {{
            width: 100% !important;
            min-width: 0 !important;
            min-height: 2.85rem !important;
            border-radius: 15px !important;
            justify-content: space-between;
        }}

        div[data-testid="stSelectbox"],
        div[data-testid="stDateInput"] {{
            width: 100%;
        }}

        div[data-testid="stDateInput"] > div,
        div[data-testid="stSelectbox"] > div {{
            width: 100%;
        }}

        .indicator-picker-box {{
            border: 1px solid {COR_BORDA};
            border-radius: 16px;
            background: #FFFFFF;
            padding: 0.8rem 0.9rem;
            min-height: 74px;
        }}

        .indicator-picker-summary {{
            font-size: 0.95rem;
            font-weight: 700;
            color: {COR_TEXTO};
            margin-bottom: 0.18rem;
        }}

        .indicator-picker-sub {{
            color: {COR_TEXTO_SUAVE};
            font-size: 0.83rem;
            line-height: 1.35;
        }}

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        div[data-testid="stDateInput"] input {{
            border-radius: 15px;
            border: 1px solid {COR_BORDA};
            background: #FFFFFF;
            color: {COR_TEXTO};
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

        div[data-testid="stCheckbox"] label {{
            font-weight: 500;
        }}

        div[data-testid="stRadio"] > div {{
            gap: 0.9rem;
        }}

        div[data-testid="stRadio"] label {{
            font-weight: 500;
        }}

        div[data-testid="stRadio"] [role="radiogroup"] {{
            justify-content: flex-end;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {COR_BORDA};
            border-radius: 18px;
            overflow: hidden;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


def format_br_number(value: float | int | None, casas: int = CASAS) -> str:
    if value is None or pd.isna(value):
        return "-"
    text = f"{float(value):,.{casas}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def format_br_date(value: pd.Timestamp | str | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return "-"
    return ts.strftime("%d/%m/%Y")


def safe_label(meta: pd.Series) -> str:
    unidade = str(meta.get("unidade") or "").strip()
    if unidade and unidade.lower() != "nan":
        return f"{meta['indicador']} ({unidade})"
    return str(meta["indicador"])


@st.cache_data(show_spinner=False, persist="disk")
def load_fred_panel(api_key: str, _version: str):
    df_long, by_key, catalog = fetch_all_fred_indicators(api_key)
    if not df_long.empty:
        df_long["data"] = pd.to_datetime(df_long["data"], errors="coerce")
        df_long["valor"] = pd.to_numeric(df_long["valor"], errors="coerce")
        df_long = df_long.dropna(subset=["data"]).sort_values(["key", "data"]).reset_index(drop=True)

    cleaned_by_key = {}
    for key, serie in by_key.items():
        tmp = serie.copy()
        if not tmp.empty:
            tmp["data"] = pd.to_datetime(tmp["data"], errors="coerce")
            tmp["valor"] = pd.to_numeric(tmp["valor"], errors="coerce")
            tmp = tmp.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
        cleaned_by_key[key] = tmp
    return catalog, df_long, cleaned_by_key


@st.cache_data(show_spinner=False, persist="disk")
def load_fred_variant_series(api_key: str, series_id: str, frequency: str):
    df = fetch_series_variant(api_key, series_id, frequency=frequency, aggregation_method="avg")
    if df.empty:
        return df
    out = df.copy()
    out["data"] = pd.to_datetime(out["data"], errors="coerce")
    out["valor"] = pd.to_numeric(out["valor"], errors="coerce")
    return out.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)


@st.cache_data(show_spinner=False, persist="disk")
def load_fred_snapshot_panel(_version: str, _snapshot_mtime: float):
    if not SNAPSHOT_US_CSV_PATH.exists() and not SNAPSHOT_US_PATH.exists():
        empty = pd.DataFrame(columns=["data", "valor", "key"])
        return pd.DataFrame(), empty, {}

    if SNAPSHOT_US_CSV_PATH.exists():
        df_long = pd.read_csv(SNAPSHOT_US_CSV_PATH, compression="gzip").copy()
    else:
        df_long = pd.read_pickle(SNAPSHOT_US_PATH).copy()
    if df_long.empty:
        return pd.DataFrame(), df_long, {}

    df_long["data"] = pd.to_datetime(df_long["data"], errors="coerce")
    df_long["valor"] = pd.to_numeric(df_long["valor"], errors="coerce")
    df_long = df_long.dropna(subset=["data"]).sort_values(["key", "data"]).reset_index(drop=True)

    catalog_cols = [col for col in df_long.columns if col not in {"data", "valor"}]
    catalog = df_long[catalog_cols].drop_duplicates("key").reset_index(drop=True)

    by_key = {}
    for key, serie in df_long.groupby("key", sort=False):
        by_key[str(key)] = serie.copy().reset_index(drop=True)

    return catalog, df_long, by_key


def normalize_text_key(value: str) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def render_indicator_picker(prefix: str, valid_keys: list[str], label_map: dict[str, str]) -> list[str]:
    selected_state_key = f"{prefix}_selected_keys"
    search_state_key = f"{prefix}_indicator_search"

    with st.popover("Escolher indicadores"):
        search_term = st.text_input(
            "Buscar indicador",
            key=search_state_key,
            placeholder="Digite para filtrar",
        )
        actions_col_a, actions_col_b = st.columns(2, gap="small")
        with actions_col_a:
            if st.button("Selecionar todos", key=f"{prefix}_select_all", use_container_width=True):
                for key in valid_keys:
                    st.session_state[f"{prefix}_check_{key}"] = True
                st.session_state[selected_state_key] = valid_keys.copy()
                st.rerun()
        with actions_col_b:
            if st.button("Limpar", key=f"{prefix}_clear_all", use_container_width=True):
                for key in valid_keys:
                    st.session_state[f"{prefix}_check_{key}"] = False
                st.session_state[selected_state_key] = []
                st.rerun()

        search_norm = normalize_text_key(search_term)
        visible_keys = [
            key for key in valid_keys
            if not search_norm or search_norm in normalize_text_key(label_map.get(key, key))
        ]

        if not visible_keys:
            st.caption("Nenhum indicador encontrado.")

        for key in visible_keys:
            st.checkbox(label_map.get(key, key), key=f"{prefix}_check_{key}")

        updated_selection = [
            key for key in valid_keys if st.session_state.get(f"{prefix}_check_{key}", False)
        ]
        st.session_state[selected_state_key] = updated_selection

    return [key for key in st.session_state.get(selected_state_key, []) if key in valid_keys]


def indicator_available_ranges(df_long: pd.DataFrame) -> pd.DataFrame:
    if df_long.empty:
        return pd.DataFrame(columns=["key", "data_min", "data_max"])
    return (
        df_long.dropna(subset=["valor"])
        .groupby("key", as_index=False)["data"]
        .agg(data_min="min", data_max="max")
    )


def preset_dates(period: str, min_date: pd.Timestamp, max_date: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    if period == "Tudo":
        return min_date, max_date
    if period == "YTD":
        start = pd.Timestamp(year=max_date.year, month=1, day=1)
        return max(start, min_date), max_date

    mapping = {
        "6M": pd.DateOffset(months=6),
        "1Y": pd.DateOffset(years=1),
        "3Y": pd.DateOffset(years=3),
        "5Y": pd.DateOffset(years=5),
        "10Y": pd.DateOffset(years=10),
    }
    offset = mapping.get(period, pd.DateOffset(years=1))
    start = max_date - offset + pd.Timedelta(days=1)
    return max(start, min_date), max_date


def clamp_date_range(
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    min_date: pd.Timestamp,
    max_date: pd.Timestamp,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.to_datetime(start, errors="coerce") if start is not None else min_date
    end = pd.to_datetime(end, errors="coerce") if end is not None else max_date
    if pd.isna(start):
        start = min_date
    if pd.isna(end):
        end = max_date
    start = max(start.normalize(), min_date.normalize())
    end = min(end.normalize(), max_date.normalize())
    if start > end:
        start = min_date.normalize()
        end = max_date.normalize()
    return start, end


def fallback_window_size(periodicidade: str) -> int:
    periodicidade = normalize_text_key(str(periodicidade))
    if periodicidade in {"trimestral", "quarterly"}:
        return 12
    if periodicidade in {"diaria", "daily"}:
        return 90
    if periodicidade in {"semanal", "weekly"}:
        return 52
    if periodicidade in {"quinzenal", "biweekly"}:
        return 26
    if periodicidade in {"anual", "annual"}:
        return 10
    return 24


def resolve_indicator_window(
    serie: pd.DataFrame,
    periodicidade: str,
    dt_ini: pd.Timestamp,
    dt_fim: pd.Timestamp,
    range_behavior: str,
) -> tuple[pd.DataFrame, str | None]:
    if serie.empty:
        return serie.copy(), "Sem dados disponíveis para este indicador."

    exact = serie[(serie["data"] >= dt_ini) & (serie["data"] <= dt_fim)].copy()
    if not exact.empty:
        return exact.reset_index(drop=True), None

    if range_behavior == "Intervalo exato":
        return exact, (
            f"Sem dados para este indicador no intervalo selecionado. Disponível entre "
            f"{format_br_date(serie['data'].min())} e {format_br_date(serie['data'].max())}."
        )

    n_points = fallback_window_size(periodicidade)
    nearest = serie[serie["data"] <= dt_fim].tail(n_points).copy()
    if nearest.empty:
        nearest = serie.head(n_points).copy()
    return nearest.reset_index(drop=True), (
        f"Sem pontos no intervalo exato. Mostrando as {len(nearest)} observações mais próximas "
        f"até {format_br_date(nearest['data'].max())}."
    )


def normalize_base_100(serie: pd.DataFrame) -> pd.DataFrame:
    out = serie.copy()
    valid = out["valor"].dropna()
    if valid.empty or float(valid.iloc[0]) == 0:
        return out
    out["valor"] = (out["valor"] / float(valid.iloc[0])) * 100
    return out


def metric_delta_parts(serie: pd.DataFrame) -> tuple[str, str, str]:
    valid = serie.dropna(subset=["valor"]).sort_values("data")
    if len(valid) < 2:
        return "", "", "metric-neutral"
    last_value = float(valid.iloc[-1]["valor"])
    prev_value = float(valid.iloc[-2]["valor"])
    delta_abs = last_value - prev_value
    pct_text = "n/d"
    if prev_value != 0:
        pct_text = f"{delta_abs / abs(prev_value) * 100:+.2f}%".replace(".", ",")
    abs_text = f"Δ {format_br_number(delta_abs, CASAS)}"
    css = "metric-neutral"
    if delta_abs > 0:
        css = "metric-pos"
    elif delta_abs < 0:
        css = "metric-neg"
    return abs_text, pct_text, css


def _line_segments(df_plot: pd.DataFrame) -> Iterable[tuple[pd.DataFrame, str]]:
    work = df_plot[["data", "valor"]].dropna().sort_values("data").copy()
    if work.empty:
        return []
    signs = np.where(work["valor"] >= 0, 1, -1)
    segment_ids = [0]
    for i in range(1, len(work)):
        segment_ids.append(segment_ids[-1] + int(signs[i] != signs[i - 1]))
    work["segment"] = segment_ids
    return [
        (chunk, COR_POSITIVA if float(chunk["valor"].iloc[-1]) >= 0 else COR_NEGATIVA)
        for _, chunk in work.groupby("segment")
    ]


def build_indicator_chart(serie: pd.DataFrame) -> go.Figure:
    df_plot = serie.dropna(subset=["data", "valor"]).copy()
    fig = go.Figure()
    segments = list(_line_segments(df_plot))
    if not segments and not df_plot.empty:
        segments = [(df_plot, COR_POSITIVA)]
    for chunk, color in segments:
        fig.add_trace(
            go.Scatter(
                x=chunk["data"],
                y=chunk["valor"],
                mode="lines+markers",
                line=dict(color=color, width=2.8),
                marker=dict(size=5, color=color),
                hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.2f}<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        height=310,
        margin=dict(l=10, r=10, t=0, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COR_TEXTO, family="Segoe UI, Arial, sans-serif"),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="rgba(16,36,62,0.08)", zeroline=False, title=None, showline=False, tickfont=dict(color=COR_TEXTO_SUAVE)),
        yaxis=dict(showgrid=True, gridcolor="rgba(16,36,62,0.08)", zeroline=True, zerolinecolor="rgba(16,36,62,0.16)", title=None, showline=False, tickfont=dict(color=COR_TEXTO_SUAVE)),
    )
    return fig


st.markdown(
    """
    <div class="macro-top">
        <div class="macro-title">Painel Macro EUA</div>
        <p class="macro-subtitle">Indicadores selecionados do FRED, organizados por grupos e prontos para análise macro dos Estados Unidos.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

snapshot_mtime = (
    SNAPSHOT_US_CSV_PATH.stat().st_mtime
    if SNAPSHOT_US_CSV_PATH.exists()
    else (SNAPSHOT_US_PATH.stat().st_mtime if SNAPSHOT_US_PATH.exists() else 0.0)
)

try:
    if SNAPSHOT_US_CSV_PATH.exists() or SNAPSHOT_US_PATH.exists():
        catalog, df_long, by_key = load_fred_snapshot_panel(DATA_PIPELINE_VERSION, snapshot_mtime)
    else:
        catalog, df_long, by_key = load_fred_panel(DEFAULT_FRED_API_KEY, DATA_PIPELINE_VERSION)
except Exception as exc:
    st.error(f"Não foi possível carregar os dados do FRED agora. Detalhe: {exc}")
    st.stop()
ranges_df = indicator_available_ranges(df_long)
meta_by_key = catalog.drop_duplicates("key").set_index("key")

groups = list(catalog["grupo"].dropna().drop_duplicates())
if "fred_group" not in st.session_state or st.session_state["fred_group"] not in groups:
    st.session_state["fred_group"] = groups[0]
active_group = st.session_state["fred_group"]
group_catalog = catalog[catalog["grupo"] == active_group].copy()
valid_keys_for_group = list(group_catalog["key"])

if "fred_selected_keys" not in st.session_state:
    st.session_state["fred_selected_keys"] = valid_keys_for_group.copy()
if "fred_group_last_applied" not in st.session_state:
    st.session_state["fred_group_last_applied"] = active_group
if "fred_period" not in st.session_state:
    st.session_state["fred_period"] = "1Y"
if "fred_compare_base100" not in st.session_state:
    st.session_state["fred_compare_base100"] = False
if "fred_dt_ini_value" not in st.session_state:
    st.session_state["fred_dt_ini_value"] = pd.Timestamp("2000-01-01").date()
if "fred_dt_fim_value" not in st.session_state:
    st.session_state["fred_dt_fim_value"] = pd.Timestamp.today().normalize().date()
if "fred_dt_ini_input" not in st.session_state:
    st.session_state["fred_dt_ini_input"] = st.session_state["fred_dt_ini_value"]
if "fred_dt_fim_input" not in st.session_state:
    st.session_state["fred_dt_fim_input"] = st.session_state["fred_dt_fim_value"]

col_group, col_ind, col_period, col_start, col_end = st.columns([1, 1, 1, 1, 1], gap="small")

with col_group:
    st.markdown('<div class="filter-label">Grupo</div>', unsafe_allow_html=True)
    selected_group = st.selectbox("Grupo", groups, key="fred_group", label_visibility="collapsed")
    is_inflation_group = normalize_text_key(selected_group) == "inflacao"
    if "fred_frequency_filter" not in st.session_state:
        st.session_state["fred_frequency_filter"] = "Todas"
    if is_inflation_group:
        st.markdown('<div class="filter-label" style="margin-top:0.55rem;">Frequ&ecirc;ncia</div>', unsafe_allow_html=True)
        st.selectbox(
            "Frequencia",
            FREQ_OPTIONS_US,
            key="fred_frequency_filter",
            label_visibility="collapsed",
        )
    else:
        st.session_state["fred_frequency_filter"] = "Todas"

group_catalog = catalog[catalog["grupo"] == selected_group].copy()
valid_keys_for_group = list(group_catalog["key"])
previous_group = st.session_state.get("fred_group_last_applied")
if previous_group != selected_group:
    st.session_state["fred_selected_keys"] = valid_keys_for_group.copy()
    st.session_state["fred_group_last_applied"] = selected_group

current_selected = [key for key in st.session_state.get("fred_selected_keys", []) if key in valid_keys_for_group]
st.session_state["fred_selected_keys"] = current_selected
label_map = {row["key"]: safe_label(row) for _, row in group_catalog.iterrows()}
for key in valid_keys_for_group:
    checkbox_state_key = f"fred_check_{key}"
    if previous_group != selected_group or checkbox_state_key not in st.session_state:
        st.session_state[checkbox_state_key] = key in current_selected

with col_ind:
    st.markdown('<div class="filter-label">Indicadores</div>', unsafe_allow_html=True)
    selected_keys = render_indicator_picker("fred", valid_keys_for_group, label_map)

if not selected_keys:
    st.info("Selecione ao menos um indicador para visualizar os dados.")
    st.stop()

with col_period:
    st.markdown('<div class="filter-label">Per&iacute;odo</div>', unsafe_allow_html=True)
    period = st.selectbox("Periodo", PERIOD_OPTIONS, key="fred_period", label_visibility="collapsed")
selected_frequency = st.session_state.get("fred_frequency_filter", "Todas")

selected_range_rows = ranges_df[ranges_df["key"].isin(selected_keys)].copy()
if selected_range_rows.empty:
    selected_range_rows = ranges_df[ranges_df["key"].isin(valid_keys_for_group)].copy()
if selected_range_rows.empty:
    global_min = pd.Timestamp.today().normalize()
    global_max = pd.Timestamp.today().normalize()
else:
    global_min = selected_range_rows["data_min"].min().normalize()
    global_max = selected_range_rows["data_max"].max().normalize()

signature = (selected_group, tuple(selected_keys), period)
if st.session_state.get("fred_period_signature") != signature:
    preset_ini, preset_fim = preset_dates(period, global_min, global_max)
    st.session_state["fred_dt_ini_value"] = preset_ini.date()
    st.session_state["fred_dt_fim_value"] = preset_fim.date()
    st.session_state["fred_dt_ini_input"] = preset_ini.date()
    st.session_state["fred_dt_fim_input"] = preset_fim.date()
    st.session_state["fred_period_signature"] = signature

with col_start:
    st.markdown('<div class="filter-label">In&iacute;cio</div>', unsafe_allow_html=True)
    dt_ini_value = st.date_input(
        "Início",
        min_value=global_min.date(),
        max_value=global_max.date(),
        key="fred_dt_ini_input",
        format="YYYY/MM/DD",
        label_visibility="collapsed",
    )

with col_end:
    st.markdown('<div class="filter-label">Fim</div>', unsafe_allow_html=True)
    dt_fim_value = st.date_input(
        "Fim",
        min_value=global_min.date(),
        max_value=global_max.date(),
        key="fred_dt_fim_input",
        format="YYYY/MM/DD",
        label_visibility="collapsed",
    )

if normalize_text_key(selected_group) == "inflacao" and selected_frequency != "Todas":
    selected_keys = [key for key in selected_keys if selected_frequency in INFLATION_FREQ_VARIANTS.get(str(key), {})]
    if not selected_keys:
        st.info(f"Nenhum indicador de Inflação disponível na frequência '{selected_frequency}'.")
        st.stop()

row_a, row_b, row_c, row_d, row_e = st.columns(5, gap="medium")
with row_a:
    st.markdown('<div class="filter-action filter-row-bottom"></div>', unsafe_allow_html=True)
    compare_base100 = st.checkbox("Comparar (base 100)", key="fred_compare_base100")
with row_b:
    st.markdown("", unsafe_allow_html=True)
with row_c:
    st.markdown("", unsafe_allow_html=True)
with row_d:
    st.markdown("", unsafe_allow_html=True)
with row_e:
    st.markdown("", unsafe_allow_html=True)

dt_ini, dt_fim = clamp_date_range(pd.Timestamp(dt_ini_value), pd.Timestamp(dt_fim_value), global_min, global_max)
if dt_ini.date() != st.session_state["fred_dt_ini_value"] or dt_fim.date() != st.session_state["fred_dt_fim_value"]:
    st.session_state["fred_dt_ini_value"] = dt_ini.date()
    st.session_state["fred_dt_fim_value"] = dt_fim.date()
    st.rerun()

st.markdown(
    f'<p class="range-note">Dados disponíveis para a seleção atual: {format_br_date(global_min)} a {format_br_date(global_max)}.</p>',
    unsafe_allow_html=True,
)

for idx in range(0, len(selected_keys), 2):
    row_keys = selected_keys[idx : idx + 2]
    cols = st.columns(2, gap="large")

    for col_idx, key in enumerate(row_keys):
        meta = meta_by_key.loc[key]
        serie = by_key.get(key, pd.DataFrame(columns=["data", "valor"])).copy()
        periodicidade = str(meta.get("frequencia") or "")
        if normalize_text_key(selected_group) == "inflacao" and selected_frequency != "Todas":
            variant = INFLATION_FREQ_VARIANTS.get(str(key), {}).get(selected_frequency)
            if variant:
                serie = load_fred_variant_series(
                    DEFAULT_FRED_API_KEY,
                    str(variant.get("series_id")),
                    str(variant.get("frequency")),
                )
                periodicidade = selected_frequency.lower()
        if not serie.empty:
            serie["data"] = pd.to_datetime(serie["data"], errors="coerce")
            serie["valor"] = pd.to_numeric(serie["valor"], errors="coerce")
            serie = serie.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)

        serie_resolved, alert_message = resolve_indicator_window(
            serie,
            str(meta.get("frequencia", "")),
            dt_ini,
            dt_fim,
            "Mais pr?ximo dispon?vel",
        )
        if compare_base100 and not serie_resolved.empty:
            serie_resolved = normalize_base_100(serie_resolved)

        indicator_name = str(meta.get("indicador") or key)
        unit_label = "Base 100" if compare_base100 else str(meta.get("unidade") or "")
        available_min = format_br_date(serie["data"].min()) if not serie.empty else "-"
        available_max = format_br_date(serie["data"].max()) if not serie.empty else "-"
        with cols[col_idx]:
            latest_valid = serie_resolved.dropna(subset=["valor"]).sort_values("data")
            if latest_valid.empty:
                value_html = "-"
                date_html = "Última data: -"
                pill_html = '<span class="metric-pill metric-neutral">Sem variação</span>'
            else:
                last_row = latest_valid.iloc[-1]
                value_html = format_br_number(last_row["valor"], CASAS)
                date_html = f"Última data: {format_br_date(last_row['data'])}"
                delta_abs, delta_pct, delta_css = metric_delta_parts(latest_valid)
                pill_html = ""
                if delta_abs:
                    pill_html += f'<span class="metric-pill {delta_css}">{delta_abs}</span>'
                if delta_pct:
                    pill_html += f'<span class="metric-pill {delta_css}">{delta_pct}</span>'
                if not pill_html:
                    pill_html = '<span class="metric-pill metric-neutral">Sem variação</span>'

            st.markdown(
                f"""
                <div class="chart-head">
                    <div>
                        <div class="chart-title">{indicator_name}</div>
                        <p class="chart-subtitle">Disponível de {available_min} a {available_max} · Frequência: {periodicidade}</p>
                    </div>
                    <div class="metric-wrap">
                        <p class="metric-label">Último valor</p>
                        <div class="metric-value">{value_html}</div>
                        <p class="metric-date">{date_html}</p>
                        <div class="metric-pills">{pill_html}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if alert_message:
                st.markdown(f'<div class="inline-alert">{alert_message}</div>', unsafe_allow_html=True)

            if serie_resolved.empty:
                continue

            fig = build_indicator_chart(serie_resolved)
            st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "modeBarButtonsToRemove": ["toggleSpikelines"], "responsive": True})

