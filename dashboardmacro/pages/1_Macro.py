# -*- coding: utf-8 -*-
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from extrair_bcb import fetch_all_indicators, load_indicators_table


st.set_page_config(page_title="Painel Macro", page_icon="📈", layout="wide")


COR_PRIMARIA = "#0F46AB"
COR_FUNDO = "#FFFFFF"
COR_TEXTO = "#10243E"
COR_TEXTO_SUAVE = "#6B7A90"
COR_SUPERFICIE = "#FFFFFF"
COR_BORDA = "#D9E2EF"
COR_POSITIVA = "#2DBE60"
COR_NEGATIVA = "#E04F5F"
COR_INFO = "#EAF2FF"
COR_INFO_BORDA = "#C9DAF8"
CASAS = 2

BASE_DIR = Path(__file__).resolve().parents[1]
CODES_PATH = BASE_DIR / "data" / "codes.csv"
SNAPSHOT_BR_PATH = BASE_DIR / "data" / "macro_brasil_snapshot.pkl"
CACHE_DIR = BASE_DIR / ".cache_sgs"
DATA_PIPELINE_VERSION = "2026-04-15-v1"

PERIOD_OPTIONS = ["6M", "1Y", "3Y", "5Y", "10Y", "YTD", "Tudo"]
RANGE_BEHAVIOR_OPTIONS = ["Mais próximo disponível", "Intervalo exato"]
MOJIBAKE_MARKERS = ("Ã", "Â", "â", "€", "™", "\x8d", "\x81", "\x82", "\x83")


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

        .filter-card {{
            background: {COR_SUPERFICIE};
            border: 1px solid {COR_BORDA};
            border-radius: 22px;
            padding: 1.1rem 1.1rem 0.4rem 1.1rem;
            box-shadow: 0 18px 42px rgba(16, 36, 62, 0.06);
            margin-bottom: 1rem;
        }}

        .range-note {{
            color: {COR_TEXTO_SUAVE};
            font-size: 0.95rem;
            margin: 0.3rem 0 1rem 0;
        }}

        .chart-card {{
            background: {COR_SUPERFICIE};
            border: 1px solid {COR_BORDA};
            border-radius: 22px;
            padding: 1.05rem 1.05rem 0.75rem 1.05rem;
            box-shadow: 0 18px 42px rgba(16, 36, 62, 0.06);
            margin-bottom: 1.15rem;
        }}

        .chart-head {{
            display: block;
            margin-bottom: 0.7rem;
        }}

        .chart-copy {{
            margin-bottom: 0.45rem;
        }}

        .chart-title {{
            font-size: 1rem;
            font-weight: 800;
            line-height: 1.28;
            color: {COR_TEXTO};
            margin: 0 0 0.25rem 0;
            overflow-wrap: anywhere;
            word-break: break-word;
            hyphens: auto;
        }}

        .chart-subtitle {{
            color: {COR_TEXTO_SUAVE};
            font-size: 0.88rem;
            line-height: 1.35;
            margin: 0;
            overflow-wrap: anywhere;
        }}

        .metric-wrap {{
            text-align: right;
            width: 100%;
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

        .metric-row {{
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 0.35rem;
            margin-top: 0.08rem;
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

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        div[data-testid="stDateInput"] input {{
            border-radius: 15px;
            border: 1px solid {COR_BORDA};
            background: #FFFFFF;
            color: {COR_TEXTO};
        }}

        div[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
            max-width: 220px;
            background: {COR_PRIMARIA} !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        div[data-testid="stMultiSelect"] [data-baseweb="tag"] span {{
            max-width: 190px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            color: #FFFFFF !important;
        }}

        div[data-testid="stMultiSelect"] [data-baseweb="tag"] svg {{
            fill: #FFFFFF !important;
        }}

        .selection-note {{
            color: {COR_TEXTO_SUAVE};
            font-size: 0.86rem;
            line-height: 1.45;
            margin: 0.35rem 0 0.1rem 0;
            overflow-wrap: anywhere;
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
            justify-content: flex-start;
        }}

        .stDownloadButton > button {{
            background: {COR_PRIMARIA};
            color: white;
            border-radius: 12px;
            border: none;
        }}

        .stDownloadButton > button:hover {{
            background: #0C3B90;
            color: white;
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


def fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return text

    current = text.replace("\ufeff", "").replace("\u00a0", " ").strip()
    if not any(marker in current for marker in MOJIBAKE_MARKERS):
        return unicodedata.normalize("NFC", current)

    for _ in range(3):
        try:
            repaired = current.encode("latin1").decode("utf-8")
        except Exception:
            break
        if repaired == current:
            break
        current = repaired

    return unicodedata.normalize("NFC", current.replace("\u00a0", " ").strip())


def normalize_text_key(value: str) -> str:
    text = fix_mojibake(str(value or "")).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


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


def parse_flag(value: object) -> bool:
    norm = normalize_text_key(str(value or ""))
    return norm in {"sim", "s", "true", "1", "yes"}


def safe_label(meta: pd.Series) -> str:
    indicador = fix_mojibake(str(meta.get("indicador") or meta.get("nome") or meta.get("key") or "Indicador"))
    unidade = fix_mojibake(str(meta.get("unidade") or "")).strip()
    if unidade and unidade.lower() != "nan":
        return f"{indicador} ({unidade})"
    return indicador


def compact_label(meta: pd.Series, max_chars: int = 42) -> str:
    label = safe_label(meta)
    if len(label) <= max_chars:
        return label
    return label[: max_chars - 1].rstrip() + "…"


@st.cache_data(show_spinner=False, persist="disk")
def load_macro_catalog(_version: str, _codes_mtime: float):
    catalog = load_indicators_table(CODES_PATH).copy()

    for col in catalog.columns:
        if catalog[col].dtype == "object":
            catalog[col] = catalog[col].map(lambda x: fix_mojibake(x) if pd.notna(x) else x)

    return catalog


@st.cache_data(show_spinner=False, persist="disk")
def load_macro_live_subset_data(
    selected_keys: tuple[str, ...],
    dt_ini: str | None,
    dt_fim: str | None,
    _version: str,
    _codes_mtime: float,
):
    catalog = load_macro_catalog(_version, _codes_mtime)
    subset = catalog[catalog["key"].astype(str).isin(selected_keys)].copy()

    if subset.empty:
        empty = pd.DataFrame(columns=["data", "valor", "key"])
        return empty, {}

    df_long, by_key = fetch_all_indicators(
        subset,
        use_disk_cache=True,
        cache_dir=CACHE_DIR,
        ttl_hours=12,
        timeout=30,
        inicio=dt_ini,
        fim=dt_fim,
    )

    if not df_long.empty:
        for col in df_long.columns:
            if df_long[col].dtype == "object":
                df_long[col] = df_long[col].map(lambda x: fix_mojibake(x) if pd.notna(x) else x)
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
        cleaned_by_key[str(key)] = tmp

    return df_long, cleaned_by_key


@st.cache_data(show_spinner=False, persist="disk")
def load_macro_snapshot_panel(_version: str, _snapshot_mtime: float):
    if not SNAPSHOT_BR_PATH.exists():
        empty = pd.DataFrame(columns=["data", "valor", "key"])
        return empty, {}

    df_long = pd.read_pickle(SNAPSHOT_BR_PATH).copy()
    if df_long.empty:
        return df_long, {}

    for col in df_long.columns:
        if df_long[col].dtype == "object":
            df_long[col] = df_long[col].map(lambda x: fix_mojibake(x) if pd.notna(x) else x)

    df_long["data"] = pd.to_datetime(df_long["data"], errors="coerce")
    df_long["valor"] = pd.to_numeric(df_long["valor"], errors="coerce")
    df_long = df_long.dropna(subset=["data"]).sort_values(["key", "data"]).reset_index(drop=True)

    by_key = {}
    for key, serie in df_long.groupby("key", sort=False):
        by_key[str(key)] = serie[["data", "valor"]].copy().reset_index(drop=True)

    return df_long, by_key


def filter_long_frame_by_date(
    df_long: pd.DataFrame,
    selected_keys: Iterable[str],
    dt_ini: pd.Timestamp | None,
    dt_fim: pd.Timestamp | None,
) -> pd.DataFrame:
    if df_long.empty:
        return df_long.copy()

    out = df_long[df_long["key"].astype(str).isin(list(selected_keys))].copy()
    if dt_ini is not None:
        out = out[out["data"] >= pd.to_datetime(dt_ini)]
    if dt_fim is not None:
        out = out[out["data"] <= pd.to_datetime(dt_fim)]
    return out.sort_values(["key", "data"]).reset_index(drop=True)


def build_available_frame(by_key: dict[str, pd.DataFrame], selected_keys: Iterable[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for key in selected_keys:
        serie = by_key.get(str(key), pd.DataFrame(columns=["data", "valor"])).copy()
        if serie.empty:
            continue
        tmp = serie[["data", "valor"]].copy()
        tmp["key"] = str(key)
        frames.append(tmp)

    if not frames:
        return pd.DataFrame(columns=["data", "valor", "key"])
    return pd.concat(frames, ignore_index=True)


def prepare_group_catalog(catalog: pd.DataFrame) -> pd.DataFrame:
    out = catalog.copy()
    out["mostrar_dashboard"] = out.get("mostrar_dashboard", "sim").map(parse_flag)
    out["ordem"] = pd.to_numeric(out.get("ordem", 999), errors="coerce").fillna(999)
    out["grupo"] = out["grupo"].map(fix_mojibake)
    out["indicador"] = out["indicador"].map(fix_mojibake)
    out["nome"] = out["nome"].map(lambda x: fix_mojibake(x) if pd.notna(x) else x)
    out["tipo_grafico"] = out["tipo_grafico"].map(lambda x: normalize_text_key(x))
    out["periodicidade"] = out["periodicidade"].map(lambda x: normalize_text_key(x))
    out["key"] = out["key"].astype(str).str.strip()
    out = out[out["mostrar_dashboard"]].copy()
    out = out.sort_values(["grupo", "ordem", "indicador", "key"]).reset_index(drop=True)
    return out


def indicator_available_ranges(df_long: pd.DataFrame) -> pd.DataFrame:
    if df_long.empty:
        return pd.DataFrame(columns=["key", "data_min", "data_max"])
    grouped = (
        df_long.dropna(subset=["valor"])
        .groupby("key", as_index=False)["data"]
        .agg(data_min="min", data_max="max")
    )
    return grouped


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


def is_preset_period(period: str) -> bool:
    return period in {"6M", "1Y", "3Y", "5Y", "10Y", "YTD", "Tudo"}


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
    periodicidade = normalize_text_key(periodicidade)
    if periodicidade == "anual":
        return 6
    if periodicidade == "diario":
        return 90
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
        first_date = format_br_date(serie["data"].min())
        last_date = format_br_date(serie["data"].max())
        return exact, f"Sem dados para este indicador no intervalo selecionado. Disponível entre {first_date} e {last_date}."

    n_points = fallback_window_size(periodicidade)
    nearest = serie[serie["data"] <= dt_fim].tail(n_points).copy()
    if nearest.empty:
        nearest = serie.head(n_points).copy()

    last_date = format_br_date(nearest["data"].max()) if not nearest.empty else "-"
    return nearest.reset_index(drop=True), (
        f"Sem pontos no intervalo exato. Mostrando as {len(nearest)} observações mais próximas até {last_date}."
    )


def normalize_base_100(serie: pd.DataFrame) -> pd.DataFrame:
    out = serie.copy()
    valid = out["valor"].dropna()
    if valid.empty:
        return out
    base = valid.iloc[0]
    if base == 0:
        return out
    out["valor"] = (out["valor"] / base) * 100
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

    segments = []
    for _, chunk in work.groupby("segment"):
        color = COR_POSITIVA if float(chunk["valor"].iloc[-1]) >= 0 else COR_NEGATIVA
        segments.append((chunk, color))
    return segments


def simplify_display_series(serie: pd.DataFrame, max_points: int = 320) -> pd.DataFrame:
    if serie.empty or len(serie) <= max_points:
        return serie
    step = max(1, len(serie) // max_points)
    simplified = serie.iloc[::step].copy()
    if simplified.iloc[-1]["data"] != serie.iloc[-1]["data"]:
        simplified = pd.concat([simplified, serie.tail(1)], ignore_index=True)
    return simplified.drop_duplicates(subset=["data"]).reset_index(drop=True)


def build_indicator_chart(
    serie: pd.DataFrame,
    chart_type: str,
    unit_label: str,
) -> go.Figure:
    df_plot = simplify_display_series(serie.dropna(subset=["data", "valor"]).copy())
    fig = go.Figure()

    if normalize_text_key(chart_type) == "barras":
        colors = np.where(df_plot["valor"] >= 0, COR_POSITIVA, COR_NEGATIVA)
        fig.add_bar(
            x=df_plot["data"],
            y=df_plot["valor"],
            marker_color=colors,
            hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.2f}<extra></extra>",
            showlegend=False,
        )
    else:
        segments = list(_line_segments(df_plot))
        if not segments and not df_plot.empty:
            segments = [(df_plot, COR_POSITIVA)]
        line_mode = "lines" if len(df_plot) > 120 else "lines+markers"
        marker_size = 0 if line_mode == "lines" else 5
        for chunk, color in segments:
            fig.add_trace(
                go.Scatter(
                    x=chunk["data"],
                    y=chunk["valor"],
                    mode=line_mode,
                    line=dict(color=color, width=2.8),
                    marker=dict(size=marker_size, color=color),
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
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(16,36,62,0.08)",
            zeroline=False,
            title=None,
            showline=False,
            tickfont=dict(color=COR_TEXTO_SUAVE),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(16,36,62,0.08)",
            zeroline=True,
            zerolinecolor="rgba(16,36,62,0.16)",
            title=None,
            showline=False,
            tickfont=dict(color=COR_TEXTO_SUAVE),
        ),
    )
    return fig


codes_mtime = CODES_PATH.stat().st_mtime if CODES_PATH.exists() else 0.0
snapshot_mtime = SNAPSHOT_BR_PATH.stat().st_mtime if SNAPSHOT_BR_PATH.exists() else 0.0
catalog_raw = load_macro_catalog(DATA_PIPELINE_VERSION, codes_mtime)
catalog = prepare_group_catalog(catalog_raw)
meta_by_key = catalog.drop_duplicates("key").set_index("key")


st.markdown(
    """
    <div class="macro-top">
        <div class="macro-title">Painel Macro</div>
        <p class="macro-subtitle">Séries do Banco Central (SGS), organizadas por grupos e indicadores.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if catalog.empty:
    st.warning("Nenhum indicador disponível no catálogo.")
    st.stop()


groups = list(catalog["grupo"].dropna().drop_duplicates())
if "macro_group" not in st.session_state or st.session_state["macro_group"] not in groups:
    st.session_state["macro_group"] = groups[0]

active_group = st.session_state["macro_group"]
group_catalog = catalog[catalog["grupo"] == active_group].copy()
valid_keys_for_group = list(group_catalog["key"])

if "macro_selected_keys" not in st.session_state:
    st.session_state["macro_selected_keys"] = valid_keys_for_group.copy()
if "macro_group_last_applied" not in st.session_state:
    st.session_state["macro_group_last_applied"] = active_group

if "macro_period" not in st.session_state:
    st.session_state["macro_period"] = "1Y"
if "macro_range_behavior" not in st.session_state:
    st.session_state["macro_range_behavior"] = RANGE_BEHAVIOR_OPTIONS[0]
if "macro_compare_base100" not in st.session_state:
    st.session_state["macro_compare_base100"] = False
if "macro_show_table" not in st.session_state:
    st.session_state["macro_show_table"] = False
if "macro_dt_ini_value" not in st.session_state:
    st.session_state["macro_dt_ini_value"] = pd.Timestamp("2000-01-01").date()
if "macro_dt_fim_value" not in st.session_state:
    st.session_state["macro_dt_fim_value"] = pd.Timestamp.today().normalize().date()


col_group, col_ind, col_period, col_start, col_end = st.columns([1.05, 2.2, 0.95, 0.9, 0.9], gap="medium")

with col_group:
    selected_group = st.selectbox("Grupo", groups, key="macro_group")

group_catalog = catalog[catalog["grupo"] == selected_group].copy()
valid_keys_for_group = list(group_catalog["key"])
previous_group = st.session_state.get("macro_group_last_applied")
if previous_group != selected_group:
    st.session_state["macro_selected_keys"] = valid_keys_for_group.copy()
    st.session_state["macro_group_last_applied"] = selected_group

current_selected = [key for key in st.session_state.get("macro_selected_keys", []) if key in valid_keys_for_group]
if not current_selected:
    current_selected = valid_keys_for_group.copy()
st.session_state["macro_selected_keys"] = current_selected

label_map = {row["key"]: compact_label(row) for _, row in group_catalog.iterrows()}

with col_ind:
    selected_keys = st.multiselect(
        "Indicadores",
        options=valid_keys_for_group,
        format_func=lambda key: label_map.get(key, key),
        key="macro_selected_keys",
    )

if not selected_keys:
    selected_keys = valid_keys_for_group.copy()
    st.session_state["macro_selected_keys"] = selected_keys

selected_labels = [label_map.get(key, key) for key in selected_keys]
if selected_labels:
    st.markdown(
        f'<p class="selection-note">{len(selected_labels)} indicador(es) selecionado(s).</p>',
        unsafe_allow_html=True,
    )

with col_period:
    period = st.selectbox("Período", PERIOD_OPTIONS, key="macro_period")

global_min = pd.Timestamp("1960-01-01").normalize()
global_max = (pd.Timestamp.today().normalize() + pd.DateOffset(years=1)).normalize()

signature = (selected_group, tuple(selected_keys), period)
if st.session_state.get("macro_period_signature") != signature:
    preset_ini, preset_fim = preset_dates(period, pd.Timestamp("2000-01-01").normalize(), pd.Timestamp.today().normalize())
    st.session_state["macro_dt_ini_value"] = preset_ini.date()
    st.session_state["macro_dt_fim_value"] = preset_fim.date()
    st.session_state["macro_period_signature"] = signature

with col_start:
    dt_ini_value = st.date_input(
        "Início",
        min_value=global_min.date(),
        max_value=global_max.date(),
        value=st.session_state["macro_dt_ini_value"],
        key="macro_dt_ini_input",
        format="YYYY/MM/DD",
    )

with col_end:
    dt_fim_value = st.date_input(
        "Fim",
        min_value=global_min.date(),
        max_value=global_max.date(),
        value=st.session_state["macro_dt_fim_value"],
        key="macro_dt_fim_input",
        format="YYYY/MM/DD",
    )

row_a, row_gap, row_b, row_c = st.columns([0.9, 2.1, 1.0, 0.5], gap="medium")
with row_a:
    compare_base100 = st.checkbox("Comparar (base 100)", key="macro_compare_base100")
with row_gap:
    st.markdown("&nbsp;", unsafe_allow_html=True)
with row_b:
    range_behavior = st.radio(
        "Sem dados no intervalo",
        RANGE_BEHAVIOR_OPTIONS,
        key="macro_range_behavior",
        horizontal=True,
    )
with row_c:
    show_table = st.checkbox("Tabela", key="macro_show_table")

dt_ini, dt_fim = clamp_date_range(
    pd.Timestamp(dt_ini_value),
    pd.Timestamp(dt_fim_value),
    global_min,
    global_max,
)

if is_preset_period(period):
    preset_base_ini, preset_base_fim = preset_dates(period, pd.Timestamp("2000-01-01").normalize(), pd.Timestamp.today().normalize())
    dt_ini, dt_fim = clamp_date_range(preset_base_ini, preset_base_fim, global_min, global_max)

if dt_ini.date() != st.session_state["macro_dt_ini_value"] or dt_fim.date() != st.session_state["macro_dt_fim_value"]:
    st.session_state["macro_dt_ini_value"] = dt_ini.date()
    st.session_state["macro_dt_fim_value"] = dt_fim.date()
    st.rerun()

snapshot_active = SNAPSHOT_BR_PATH.exists()
if snapshot_active:
    full_df_long, full_by_key = load_macro_snapshot_panel(DATA_PIPELINE_VERSION, snapshot_mtime)
    by_key = {
        str(key): full_by_key.get(str(key), pd.DataFrame(columns=["data", "valor"])).copy()
        for key in selected_keys
    }
    available_df = build_available_frame(full_by_key, selected_keys)
    df_long = filter_long_frame_by_date(full_df_long, selected_keys, dt_ini, dt_fim)
else:
    df_long, by_key = load_macro_live_subset_data(
        tuple(selected_keys),
        dt_ini.strftime("%Y-%m-%d"),
        dt_fim.strftime("%Y-%m-%d"),
        DATA_PIPELINE_VERSION,
        codes_mtime,
    )
    available_df = build_available_frame(by_key, selected_keys)

ranges_df = indicator_available_ranges(available_df)
selected_range_rows = ranges_df[ranges_df["key"].isin(selected_keys)].copy()

if selected_range_rows.empty:
    available_min = dt_ini.normalize()
    available_max = dt_fim.normalize()
else:
    available_min = selected_range_rows["data_min"].min().normalize()
    available_max = selected_range_rows["data_max"].max().normalize()

dt_ini, dt_fim = clamp_date_range(dt_ini, dt_fim, available_min, available_max)

st.markdown(
    f'<p class="range-note">Dados disponíveis para a seleção atual: {format_br_date(available_min)} a {format_br_date(available_max)}.</p>',
    unsafe_allow_html=True,
)


table_frames: list[pd.DataFrame] = []
selected_meta = catalog[catalog["key"].isin(selected_keys)].copy()
selected_meta = selected_meta.set_index("key").loc[selected_keys].reset_index()

for idx in range(0, len(selected_keys), 2):
    row_keys = selected_keys[idx : idx + 2]
    cols = st.columns(2, gap="large")

    for col_idx, key in enumerate(row_keys):
        meta = meta_by_key.loc[key]
        serie = by_key.get(key, pd.DataFrame(columns=["data", "valor"])).copy()
        if not serie.empty:
            serie["data"] = pd.to_datetime(serie["data"], errors="coerce")
            serie["valor"] = pd.to_numeric(serie["valor"], errors="coerce")
            serie = serie.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)

        serie_resolved, alert_message = resolve_indicator_window(
            serie,
            str(meta.get("periodicidade", "")),
            dt_ini,
            dt_fim,
            range_behavior,
        )

        if compare_base100 and not serie_resolved.empty:
            serie_resolved = normalize_base_100(serie_resolved)

        chart_type = str(meta.get("tipo_grafico", "linhas"))
        indicator_name = fix_mojibake(str(meta.get("indicador") or meta.get("nome") or key))
        unit_label = "Base 100" if compare_base100 else fix_mojibake(str(meta.get("unidade") or ""))
        available_min = format_br_date(serie["data"].min()) if not serie.empty else "-"
        available_max = format_br_date(serie["data"].max()) if not serie.empty else "-"
        periodicidade = fix_mojibake(str(meta.get("periodicidade") or ""))
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
                    <div class="chart-copy">
                        <div class="chart-title">{indicator_name}</div>
                        <p class="chart-subtitle">Disponível de {available_min} a {available_max} · Frequência: {periodicidade}</p>
                    </div>
                    <div class="metric-wrap">
                        <p class="metric-label">Último valor</p>
                        <div class="metric-value">{value_html}</div>
                        <p class="metric-date">{date_html}</p>
                        <div class="metric-row">
                            <div class="metric-pills">{pill_html}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if alert_message:
                st.markdown(f'<div class="inline-alert">{alert_message}</div>', unsafe_allow_html=True)

            if serie_resolved.empty:
                continue

            fig = build_indicator_chart(serie_resolved, chart_type, unit_label)
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displaylogo": False, "modeBarButtonsToRemove": ["toggleSpikelines"], "responsive": True},
            )

            export_df = serie_resolved.copy()
            export_df["indicador"] = indicator_name
            export_df["unidade"] = unit_label
            table_frames.append(export_df)


if show_table:
    if table_frames:
        table_df = pd.concat(table_frames, ignore_index=True)
        table_df = table_df[["indicador", "data", "valor", "unidade"]].copy()
        table_df["data"] = pd.to_datetime(table_df["data"], errors="coerce").dt.strftime("%d/%m/%Y")
        table_df["valor"] = table_df["valor"].map(lambda v: format_br_number(v, CASAS))
        st.dataframe(table_df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado disponível para exibir na tabela.")
