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
SNAPSHOT_BR_CSV_PATH = BASE_DIR / "data" / "macro_brasil_snapshot.csv.gz"
CACHE_DIR = BASE_DIR / ".cache_sgs"
DATA_PIPELINE_VERSION = "2026-05-07-v1"
LEAD_MESES_M1 = 12
DERIVED_DEPENDENCIES = {
    "saldo_tc_idp_12m": ["transacoes_correntes", "ide_pais_12m"],
    "m1_var_12m": ["agregado_monetario_m1"],
    "inflacao12_m1yoy": ["m1_var_12m", "ipca_12_meses", "agregado_monetario_m1"],
    "pib_efetivo_potencial_hiato": ["pib_r"],
}

PERIOD_OPTIONS = ["6M", "1Y", "3Y", "5Y", "10Y", "YTD", "Tudo"]
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


def expand_indicator_keys(selected_keys: Iterable[str]) -> list[str]:
    expanded: list[str] = []
    queue = list(selected_keys)
    seen = set()
    while queue:
        key = str(queue.pop(0))
        if key in seen:
            continue
        seen.add(key)
        expanded.append(key)
        queue.extend(DERIVED_DEPENDENCIES.get(key, []))
    return expanded


def recompute_visual_derived_series(by_key: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out = {str(key): value.copy() for key, value in by_key.items()}

    tc = out.get("transacoes_correntes", pd.DataFrame(columns=["data", "valor"])).copy()
    idp = out.get("ide_pais_12m", pd.DataFrame(columns=["data", "valor"])).copy()
    if not tc.empty and not idp.empty:
        tc["data"] = pd.to_datetime(tc["data"], errors="coerce")
        tc["valor"] = pd.to_numeric(tc["valor"], errors="coerce")
        idp["data"] = pd.to_datetime(idp["data"], errors="coerce")
        idp["valor"] = pd.to_numeric(idp["valor"], errors="coerce")
        merged = (
            tc.dropna(subset=["data", "valor"])[["data", "valor"]]
            .rename(columns={"valor": "valor_tc"})
            .merge(
                idp.dropna(subset=["data", "valor"])[["data", "valor"]].rename(columns={"valor": "valor_idp"}),
                on="data",
                how="inner",
            )
            .sort_values("data")
            .reset_index(drop=True)
        )
        if not merged.empty:
            merged["valor"] = merged["valor_idp"] + merged["valor_tc"]
            out["saldo_tc_idp_12m"] = merged[["data", "valor"]].copy()

    m1 = out.get("agregado_monetario_m1", pd.DataFrame(columns=["data", "valor"])).copy()
    if not m1.empty:
        m1["data"] = pd.to_datetime(m1["data"], errors="coerce")
        m1["valor"] = pd.to_numeric(m1["valor"], errors="coerce")
        m1 = m1.dropna(subset=["data", "valor"]).sort_values("data")
        if not m1.empty:
            m1["periodo"] = m1["data"].dt.to_period("M")
            monthly = (
                m1.groupby("periodo", as_index=False)["valor"]
                .mean()
                .sort_values("periodo")
                .reset_index(drop=True)
            )
            monthly["valor"] = monthly["valor"].pct_change(12) * 100
            monthly["data"] = monthly["periodo"].dt.to_timestamp()
            monthly = monthly.dropna(subset=["valor"])[["data", "valor"]].reset_index(drop=True)
            out["m1_var_12m"] = monthly

    ipca = out.get("ipca_12_meses", pd.DataFrame(columns=["data", "valor"])).copy()
    m1_yoy = out.get("m1_var_12m", pd.DataFrame(columns=["data", "valor"])).copy()
    if not ipca.empty and not m1_yoy.empty:
        ipca["data"] = pd.to_datetime(ipca["data"], errors="coerce")
        ipca["valor"] = pd.to_numeric(ipca["valor"], errors="coerce")
        m1_yoy["data"] = pd.to_datetime(m1_yoy["data"], errors="coerce")
        m1_yoy["valor"] = pd.to_numeric(m1_yoy["valor"], errors="coerce")
        ipca = ipca.dropna(subset=["data", "valor"]).sort_values("data")
        m1_yoy = m1_yoy.dropna(subset=["data", "valor"]).sort_values("data")
        if not ipca.empty and not m1_yoy.empty:
            ipca["ano_mes"] = ipca["data"].dt.to_period("M")
            m1_yoy["data_lead"] = m1_yoy["data"] + pd.DateOffset(months=LEAD_MESES_M1)
            m1_yoy["ano_mes"] = m1_yoy["data_lead"].dt.to_period("M")

            ipca_monthly = (
                ipca.groupby("ano_mes", as_index=False)
                .tail(1)[["ano_mes", "valor"]]
                .rename(columns={"valor": "ipca"})
                .sort_values("ano_mes")
                .reset_index(drop=True)
            )
            m1_monthly = (
                m1_yoy.groupby("ano_mes", as_index=False)
                .tail(1)[["ano_mes", "valor"]]
                .rename(columns={"valor": "m1_lead"})
                .sort_values("ano_mes")
                .reset_index(drop=True)
            )

            min_per = min(ipca_monthly["ano_mes"].min(), m1_monthly["ano_mes"].min())
            max_per = max(ipca_monthly["ano_mes"].max(), m1_monthly["ano_mes"].max())
            calendar = pd.DataFrame({"ano_mes": pd.period_range(min_per, max_per, freq="M")})
            merged = (
                calendar.merge(ipca_monthly, on="ano_mes", how="left")
                .merge(m1_monthly, on="ano_mes", how="left")
                .sort_values("ano_mes")
                .reset_index(drop=True)
            )
            if not merged.empty:
                merged["data"] = merged["ano_mes"].dt.to_timestamp()
                merged["valor"] = merged["ipca"].combine_first(merged["m1_lead"])
                out["inflacao12_m1yoy"] = merged[["data", "valor"]].dropna(subset=["valor"]).reset_index(drop=True)

    pib_base = out.get("pib_r", pd.DataFrame(columns=["data", "valor"])).copy()
    if not pib_base.empty:
        gap_df = build_pib_potential_gap_frame(pib_base)
        if not gap_df.empty:
            out["pib_efetivo_potencial_hiato"] = gap_df

    return out


def _quadratic_trend(values: np.ndarray, window: int = 86, min_points: int = 24) -> np.ndarray:
    y = np.asarray(values, dtype=float)
    n = len(y)
    out = np.full(n, np.nan, dtype=float)
    if n < 3:
        return out

    for i in range(n):
        start = max(0, i - window + 1)
        y_slice = y[start : i + 1]
        mask = np.isfinite(y_slice)
        if mask.sum() < min_points:
            continue

        # Quadratic trend estimated on rolling window, predicted at current endpoint.
        x = np.linspace(-1.0, 1.0, len(y_slice), dtype=float)
        coeffs = np.polyfit(x[mask], y_slice[mask], 2)
        out[i] = np.polyval(coeffs, x[-1])

    return out


def build_pib_potential_gap_frame(serie: pd.DataFrame) -> pd.DataFrame:
    base = serie.copy()
    if base.empty:
        return pd.DataFrame(columns=["data", "valor", "valor_efetivo", "valor_potencial", "hiato_produto"])

    base["data"] = pd.to_datetime(base["data"], errors="coerce")
    base["valor"] = pd.to_numeric(base["valor"], errors="coerce")
    base = base.dropna(subset=["data", "valor"]).sort_values("data").reset_index(drop=True)
    if len(base) < 8:
        return pd.DataFrame(columns=["data", "valor", "valor_efetivo", "valor_potencial", "hiato_produto"])

    log_values = np.log(base["valor"].to_numpy(dtype=float))
    trend_log = _quadratic_trend(log_values)
    if not np.isfinite(trend_log).any():
        return pd.DataFrame(columns=["data", "valor", "valor_efetivo", "valor_potencial", "hiato_produto"])

    potencial = np.exp(trend_log)
    hiato = ((base["valor"].to_numpy(dtype=float) / potencial) - 1.0) * 100.0

    out = pd.DataFrame(
        {
            "data": base["data"],
            "valor": hiato,
            "valor_efetivo": base["valor"].to_numpy(dtype=float),
            "valor_potencial": potencial,
            "hiato_produto": hiato,
        }
    )
    return out.replace([np.inf, -np.inf], np.nan).dropna(subset=["data"]).reset_index(drop=True)


def _read_snapshot_frame(csv_path: Path, pickle_path: Path) -> pd.DataFrame:
    if csv_path.exists():
        df = pd.read_csv(csv_path, compression="gzip")
        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")
        for col in ("valor", "valor_efetivo", "valor_potencial", "hiato_produto"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    if pickle_path.exists():
        return pd.read_pickle(pickle_path)
    return pd.DataFrame()


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
    expanded_keys = expand_indicator_keys(selected_keys)
    subset = catalog[catalog["key"].astype(str).isin(expanded_keys)].copy()

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
            if "valor" in tmp.columns:
                tmp["valor"] = pd.to_numeric(tmp["valor"], errors="coerce")
            for col in ("valor_efetivo", "valor_potencial", "hiato_produto"):
                if col in tmp.columns:
                    tmp[col] = pd.to_numeric(tmp[col], errors="coerce")
            tmp = tmp.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
        cleaned_by_key[str(key)] = tmp

    return df_long, cleaned_by_key


def has_large_monthly_gap(serie: pd.DataFrame, min_consecutive_missing: int = 24) -> bool:
    if serie is None or serie.empty or "data" not in serie.columns:
        return False

    tmp = serie.copy()
    tmp["data"] = pd.to_datetime(tmp["data"], errors="coerce")
    tmp = tmp.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
    if tmp.empty:
        return False

    month_index = pd.period_range(tmp["data"].min().to_period("M"), tmp["data"].max().to_period("M"), freq="M")
    observed = set(tmp["data"].dt.to_period("M"))
    run = 0
    for month in month_index:
        if month in observed:
            run = 0
        else:
            run += 1
            if run >= min_consecutive_missing:
                return True
    return False


def refresh_m1_related_keys_if_needed(
    by_key: dict[str, pd.DataFrame],
    _version: str,
    _codes_mtime: float,
) -> dict[str, pd.DataFrame]:
    m1_snapshot = by_key.get("agregado_monetario_m1", pd.DataFrame())
    if not has_large_monthly_gap(m1_snapshot, min_consecutive_missing=24):
        return by_key

    catalog = load_macro_catalog(_version, _codes_mtime)
    repair_keys = ["agregado_monetario_m1", "m1_var_12m", "ipca_12_meses", "inflacao12_m1yoy"]
    subset = catalog[catalog["key"].astype(str).isin(repair_keys)].copy()
    if subset.empty:
        return by_key

    _, live_by_key = fetch_all_indicators(
        subset,
        use_disk_cache=False,
        cache_dir=CACHE_DIR,
        ttl_hours=0,
        timeout=30,
        inicio=None,
        fim=None,
    )
    live_by_key = recompute_visual_derived_series({str(k): v.copy() for k, v in live_by_key.items()})

    repaired = {str(k): v.copy() for k, v in by_key.items()}
    for key in repair_keys:
        serie = live_by_key.get(key, pd.DataFrame()).copy()
        if not serie.empty:
            serie["data"] = pd.to_datetime(serie["data"], errors="coerce")
            if "valor" in serie.columns:
                serie["valor"] = pd.to_numeric(serie["valor"], errors="coerce")
            for col in ("valor_efetivo", "valor_potencial", "hiato_produto"):
                if col in serie.columns:
                    serie[col] = pd.to_numeric(serie[col], errors="coerce")
            serie = serie.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
            repaired[key] = serie

    return repaired


@st.cache_data(show_spinner=False, persist="disk")
def load_macro_snapshot_panel(_version: str, _snapshot_mtime: float):
    if not SNAPSHOT_BR_CSV_PATH.exists() and not SNAPSHOT_BR_PATH.exists():
        empty = pd.DataFrame(columns=["data", "valor", "key"])
        return empty, {}

    df_long = _read_snapshot_frame(SNAPSHOT_BR_CSV_PATH, SNAPSHOT_BR_PATH).copy()
    if df_long.empty:
        return df_long, {}

    for col in df_long.columns:
        if df_long[col].dtype == "object":
            df_long[col] = df_long[col].map(lambda x: fix_mojibake(x) if pd.notna(x) else x)

    df_long["data"] = pd.to_datetime(df_long["data"], errors="coerce")
    if "valor" in df_long.columns:
        df_long["valor"] = pd.to_numeric(df_long["valor"], errors="coerce")
    for col in ("valor_efetivo", "valor_potencial", "hiato_produto"):
        if col in df_long.columns:
            df_long[col] = pd.to_numeric(df_long[col], errors="coerce")
    df_long = df_long.dropna(subset=["data"]).sort_values(["key", "data"]).reset_index(drop=True)

    by_key = {}
    for key, serie in df_long.groupby("key", sort=False):
        by_key[str(key)] = serie.copy().reset_index(drop=True)

    codes_mtime = CODES_PATH.stat().st_mtime if CODES_PATH.exists() else 0.0
    by_key = refresh_m1_related_keys_if_needed(by_key, _version, codes_mtime)

    frames = []
    for key, serie in by_key.items():
        if serie.empty:
            continue
        tmp = serie.copy()
        tmp["key"] = str(key)
        frames.append(tmp)
    if frames:
        df_long = pd.concat(frames, ignore_index=True)
        df_long = df_long.dropna(subset=["data"]).sort_values(["key", "data"]).reset_index(drop=True)

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
    previous_tail = None
    for _, chunk in work.groupby("segment"):
        chunk = chunk.copy()
        if previous_tail is not None:
            chunk = pd.concat([previous_tail, chunk], ignore_index=True)
        color = COR_POSITIVA if float(chunk["valor"].iloc[-1]) >= 0 else COR_NEGATIVA
        segments.append((chunk, color))
        previous_tail = chunk.tail(1).copy()
    return segments


def simplify_display_series(serie: pd.DataFrame, max_points: int = 320) -> pd.DataFrame:
    if serie.empty or len(serie) <= max_points:
        return serie
    step = max(1, len(serie) // max_points)
    simplified = serie.iloc[::step].copy()
    if simplified.iloc[-1]["data"] != serie.iloc[-1]["data"]:
        simplified = pd.concat([simplified, serie.tail(1)], ignore_index=True)
    return simplified.drop_duplicates(subset=["data"]).reset_index(drop=True)


def insert_line_breaks_for_gaps(serie: pd.DataFrame, max_gap_days: int = 45) -> pd.DataFrame:
    if serie.empty:
        return serie
    tmp = serie.copy()
    tmp["data"] = pd.to_datetime(tmp["data"], errors="coerce")
    tmp = tmp.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
    if len(tmp) < 2:
        return tmp

    rows = [tmp.iloc[0].copy()]
    for i in range(1, len(tmp)):
        prev = tmp.iloc[i - 1]
        curr = tmp.iloc[i]
        gap_days = (curr["data"] - prev["data"]).days
        if gap_days > max_gap_days:
            gap_row = curr.copy()
            gap_row["data"] = prev["data"] + pd.Timedelta(days=1)
            if "valor" in gap_row.index:
                gap_row["valor"] = np.nan
            rows.append(gap_row)
        rows.append(curr.copy())

    out = pd.DataFrame(rows).reset_index(drop=True)
    return out


def build_indicator_chart(
    serie: pd.DataFrame,
    chart_type: str,
    unit_label: str,
    series_key: str | None = None,
) -> go.Figure:
    base_plot = serie.dropna(subset=["data", "valor"]).copy()
    if series_key == "saldo_tc_idp_12m":
        df_plot = base_plot.sort_values("data").reset_index(drop=True)
    else:
        df_plot = simplify_display_series(base_plot)
    fig = go.Figure()

    if series_key == "m1_var_12m":
        df_plot = insert_line_breaks_for_gaps(df_plot, max_gap_days=45)
        segments = list(_line_segments(df_plot))
        if not segments and not df_plot.empty:
            segments = [(df_plot, COR_POSITIVA if float(df_plot["valor"].iloc[-1]) >= 0 else COR_NEGATIVA)]
        for chunk, color in segments:
            fig.add_trace(
                go.Scatter(
                    x=chunk["data"],
                    y=chunk["valor"],
                    mode="lines",
                    line=dict(color=color, width=2.4),
                    hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.2f}<extra></extra>",
                    showlegend=False,
                )
            )
    elif normalize_text_key(chart_type) == "barras":
        colors = np.where(df_plot["valor"] >= 0, COR_POSITIVA, COR_NEGATIVA)
        fig.add_bar(
            x=df_plot["data"],
            y=df_plot["valor"],
            marker_color=colors,
            marker_line_width=0,
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
            zerolinecolor="rgba(16,36,62,0.22)" if series_key == "saldo_tc_idp_12m" else "rgba(16,36,62,0.16)",
            zerolinewidth=1.4 if series_key == "saldo_tc_idp_12m" else 1,
            title=None,
            showline=False,
            tickfont=dict(color=COR_TEXTO_SUAVE),
        ),
    )
    return fig


def build_inflation_vs_m1_chart(
    ipca_series: pd.DataFrame,
    m1_series: pd.DataFrame,
) -> go.Figure:
    fig = go.Figure()
    ipca_plot = simplify_display_series(ipca_series.dropna(subset=["data", "valor"]).sort_values("data").copy())
    m1_plot = simplify_display_series(m1_series.dropna(subset=["data", "valor"]).sort_values("data").copy())
    ipca_plot = insert_line_breaks_for_gaps(ipca_plot, max_gap_days=45)
    m1_plot = insert_line_breaks_for_gaps(m1_plot, max_gap_days=45)

    fig.add_trace(
        go.Scatter(
            x=ipca_plot["data"],
            y=ipca_plot["valor"],
            mode="lines",
            name="IPCA 12m",
            line=dict(color=COR_PRIMARIA, width=2.4),
            hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.2f}<extra>IPCA 12m</extra>",
            yaxis="y",
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=m1_plot["data"],
            y=m1_plot["valor"],
            mode="lines",
            name="M1 Var. 12m (lead 12m)",
            line=dict(color=COR_POSITIVA, width=2.2, dash="dash"),
            hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.2f}<extra>M1 Var. 12m (lead 12m)</extra>",
            yaxis="y2",
            showlegend=True,
        )
    )

    fig.update_layout(
        height=310,
        margin=dict(l=10, r=10, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COR_TEXTO, family="Segoe UI, Arial, sans-serif"),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="rgba(16,36,62,0.08)",
            borderwidth=1,
            font=dict(size=11),
        ),
        hovermode="x",
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
            title="IPCA (%)",
            showline=False,
            tickfont=dict(color=COR_TEXTO_SUAVE),
            title_font=dict(color=COR_PRIMARIA, size=12),
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
            title="M1 YoY (%)",
            tickfont=dict(color=COR_POSITIVA),
            title_font=dict(color=COR_POSITIVA, size=12),
        ),
    )
    return fig


def build_pib_effective_potential_gap_chart(serie: pd.DataFrame) -> go.Figure:
    df_plot = serie.copy()
    df_plot["data"] = pd.to_datetime(df_plot["data"], errors="coerce")
    for col in ("valor_efetivo", "valor_potencial", "hiato_produto"):
        if col in df_plot.columns:
            df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")
    df_plot = df_plot.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)

    fig = go.Figure()
    if df_plot.empty:
        return fig

    bars = df_plot.dropna(subset=["hiato_produto"]).copy()
    hiato_abs_max = 0.0
    if not bars.empty:
        hiato_abs_max = float(np.nanmax(np.abs(bars["hiato_produto"].to_numpy(dtype=float))))
        bar_colors = np.where(bars["hiato_produto"] >= 0, COR_POSITIVA, COR_NEGATIVA)
        fig.add_bar(
            x=bars["data"],
            y=bars["hiato_produto"],
            name="Hiato",
            yaxis="y2",
            marker_color=bar_colors,
            marker_line_width=0,
            opacity=0.32,
            width=22 * 24 * 60 * 60 * 1000,
            hovertemplate="%{x|%d/%m/%Y}<br>Hiato: %{y:,.2f}%<extra></extra>",
        )

    efetivo = df_plot.dropna(subset=["valor_efetivo"])
    if not efetivo.empty:
        fig.add_trace(
            go.Scatter(
                x=efetivo["data"],
                y=efetivo["valor_efetivo"],
                mode="lines",
                name="PIB efetivo",
                line=dict(color=COR_PRIMARIA, width=2.6),
                hovertemplate="%{x|%d/%m/%Y}<br>PIB efetivo: %{y:,.2f}<extra></extra>",
                yaxis="y",
            )
        )

    potencial = df_plot.dropna(subset=["valor_potencial"])
    if not potencial.empty:
        fig.add_trace(
            go.Scatter(
                x=potencial["data"],
                y=potencial["valor_potencial"],
                mode="lines",
                name="PIB potencial",
                line=dict(color="#D67A2C", width=2.3),
                hovertemplate="%{x|%d/%m/%Y}<br>PIB potencial: %{y:,.2f}<extra></extra>",
                yaxis="y",
            )
        )

    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COR_TEXTO, family="Segoe UI, Arial, sans-serif"),
        barmode="overlay",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="rgba(16,36,62,0.08)",
            borderwidth=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(16,36,62,0.08)",
            zeroline=False,
            title=None,
            showline=False,
            tickformat="%b %Y",
            tickfont=dict(color=COR_TEXTO_SUAVE),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(16,36,62,0.08)",
            zeroline=False,
            title=None,
            tickformat="~s",
            tickfont=dict(color=COR_TEXTO_SUAVE),
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=True,
            zerolinecolor="rgba(16,36,62,0.16)",
            title="Hiato (%)",
            tickfont=dict(color=COR_TEXTO_SUAVE),
            title_font=dict(color=COR_TEXTO_SUAVE, size=12),
            tickformat=".1f",
            ticksuffix="%",
        ),
    )

    if hiato_abs_max > 0:
        upper = max(6.0, round(hiato_abs_max * 1.25, 1))
        fig.update_layout(yaxis2=dict(range=[-upper, upper]))
    return fig


def build_special_comparison_df(key: str, by_key: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if key != "inflacao12_m1yoy":
        return pd.DataFrame(), pd.DataFrame()

    ipca_12m = by_key.get("ipca_12_meses", pd.DataFrame(columns=["data", "valor"])).copy()
    m1_yoy = by_key.get("m1_var_12m", pd.DataFrame(columns=["data", "valor"])).copy()
    for df in (ipca_12m, m1_yoy):
        if not df.empty:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
            df.dropna(subset=["data", "valor"], inplace=True)
            df.sort_values("data", inplace=True)
            df.reset_index(drop=True, inplace=True)

    if ipca_12m.empty and m1_yoy.empty:
        return pd.DataFrame(), pd.DataFrame()

    def _monthly_last(df: pd.DataFrame, date_col: str = "data") -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["ano_mes", "valor"])
        monthly = df.copy()
        monthly["ano_mes"] = monthly[date_col].dt.to_period("M")
        monthly = (
            monthly.groupby("ano_mes", as_index=False)
            .tail(1)[["ano_mes", "valor"]]
            .sort_values("ano_mes")
            .reset_index(drop=True)
        )
        return monthly

    m1_yoy = m1_yoy.copy()
    if not m1_yoy.empty:
        m1_yoy["data_lead"] = m1_yoy["data"] + pd.DateOffset(months=LEAD_MESES_M1)

    ipca_monthly = _monthly_last(ipca_12m)
    m1_monthly = _monthly_last(m1_yoy, "data_lead")

    periods = []
    if not ipca_monthly.empty:
        periods.extend(ipca_monthly["ano_mes"].tolist())
    if not m1_monthly.empty:
        periods.extend(m1_monthly["ano_mes"].tolist())
    if not periods:
        return pd.DataFrame(), pd.DataFrame()

    calendar = pd.DataFrame({"ano_mes": pd.period_range(min(periods), max(periods), freq="M")})
    ipca_plot = calendar.merge(ipca_monthly, on="ano_mes", how="left")
    m1_plot = calendar.merge(m1_monthly, on="ano_mes", how="left")
    ipca_plot["data"] = ipca_plot["ano_mes"].dt.to_timestamp()
    m1_plot["data"] = m1_plot["ano_mes"].dt.to_timestamp()

    ipca_plot = ipca_plot.dropna(subset=["valor"])[["data", "valor"]].reset_index(drop=True)
    m1_plot = m1_plot.dropna(subset=["valor"])[["data", "valor"]].reset_index(drop=True)
    return ipca_plot, m1_plot


def load_hiato_fallback_series(_codes_mtime: float, _version: str) -> pd.DataFrame:
    _, dep_by_key = load_macro_live_subset_data(
        ("pib_r",),
        None,
        None,
        _version,
        _codes_mtime,
    )
    dep_by_key = recompute_visual_derived_series(dep_by_key)
    serie = dep_by_key.get("pib_efetivo_potencial_hiato", pd.DataFrame()).copy()
    if not serie.empty:
        serie["data"] = pd.to_datetime(serie["data"], errors="coerce")
        if "valor" in serie.columns:
            serie["valor"] = pd.to_numeric(serie["valor"], errors="coerce")
        for col in ("valor_efetivo", "valor_potencial", "hiato_produto"):
            if col in serie.columns:
                serie[col] = pd.to_numeric(serie[col], errors="coerce")
        serie = serie.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
    return serie


def load_pib_base_series(
    dt_ini: pd.Timestamp,
    dt_fim: pd.Timestamp,
    _codes_mtime: float,
    _version: str,
) -> pd.DataFrame:
    serie = pd.DataFrame(columns=["data", "valor"])
    if SNAPSHOT_BR_CSV_PATH.exists() or SNAPSHOT_BR_PATH.exists():
        snapshot_df = _read_snapshot_frame(SNAPSHOT_BR_CSV_PATH, SNAPSHOT_BR_PATH)
        if not snapshot_df.empty and "key" in snapshot_df.columns:
            serie = snapshot_df[snapshot_df["key"].astype(str) == "pib_r"].copy()

    serie = clean_indicator_series(serie)
    if not serie.empty:
        return serie

    _, dep_by_key = load_macro_live_subset_data(
        ("pib_r",),
        None,
        None,
        _version,
        _codes_mtime,
    )
    serie = clean_indicator_series(dep_by_key.get("pib_r", pd.DataFrame()).copy())
    if not serie.empty:
        return serie

    _, dep_by_key = load_macro_live_subset_data(
        ("pib_r",),
        dt_ini.strftime("%Y-%m-%d"),
        dt_fim.strftime("%Y-%m-%d"),
        _version,
        _codes_mtime,
    )
    return clean_indicator_series(dep_by_key.get("pib_r", pd.DataFrame()).copy())


def load_live_fallback_series(
    key: str,
    dt_ini: pd.Timestamp,
    dt_fim: pd.Timestamp,
    _codes_mtime: float,
    _version: str,
) -> pd.DataFrame:
    expanded = tuple(expand_indicator_keys([key]))
    _, dep_by_key = load_macro_live_subset_data(
        expanded,
        dt_ini.strftime("%Y-%m-%d"),
        dt_fim.strftime("%Y-%m-%d"),
        _version,
        _codes_mtime,
    )
    dep_by_key = recompute_visual_derived_series(dep_by_key)
    serie = dep_by_key.get(key, pd.DataFrame()).copy()
    if not serie.empty:
        serie["data"] = pd.to_datetime(serie["data"], errors="coerce")
        if "valor" in serie.columns:
            serie["valor"] = pd.to_numeric(serie["valor"], errors="coerce")
        for col in ("valor_efetivo", "valor_potencial", "hiato_produto"):
            if col in serie.columns:
                serie[col] = pd.to_numeric(serie[col], errors="coerce")
        serie = serie.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
    return serie


def clean_indicator_series(serie: pd.DataFrame) -> pd.DataFrame:
    tmp = serie.copy()
    if tmp.empty:
        return tmp
    tmp["data"] = pd.to_datetime(tmp["data"], errors="coerce")
    if "valor" in tmp.columns:
        tmp["valor"] = pd.to_numeric(tmp["valor"], errors="coerce")
    for col in ("valor_efetivo", "valor_potencial", "hiato_produto"):
        if col in tmp.columns:
            tmp[col] = pd.to_numeric(tmp[col], errors="coerce")
    return tmp.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)


def resolve_hiato_series(
    dt_ini: pd.Timestamp,
    dt_fim: pd.Timestamp,
    _codes_mtime: float,
    _version: str,
) -> tuple[pd.DataFrame, pd.DataFrame, str | None]:
    pib_base = load_pib_base_series(dt_ini, dt_fim, _codes_mtime, _version)
    serie = build_pib_potential_gap_frame(pib_base)
    serie = clean_indicator_series(serie)

    if serie.empty:
        serie = clean_indicator_series(load_hiato_fallback_series(_codes_mtime, _version))

    serie_resolved, alert_message = resolve_indicator_window(
        serie,
        "mensal",
        dt_ini,
        dt_fim,
        "Mais proximo disponivel",
    )
    if serie_resolved.empty and not serie.empty:
        serie_resolved = serie.tail(min(len(serie), 8)).reset_index(drop=True)
        alert_message = None
    return serie, serie_resolved, alert_message


codes_mtime = CODES_PATH.stat().st_mtime if CODES_PATH.exists() else 0.0
snapshot_mtime = (
    SNAPSHOT_BR_CSV_PATH.stat().st_mtime
    if SNAPSHOT_BR_CSV_PATH.exists()
    else (SNAPSHOT_BR_PATH.stat().st_mtime if SNAPSHOT_BR_PATH.exists() else 0.0)
)
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
if "macro_compare_base100" not in st.session_state:
    st.session_state["macro_compare_base100"] = False
if "macro_dt_ini_value" not in st.session_state:
    st.session_state["macro_dt_ini_value"] = pd.Timestamp("2000-01-01").date()
if "macro_dt_fim_value" not in st.session_state:
    st.session_state["macro_dt_fim_value"] = pd.Timestamp.today().normalize().date()
if "macro_dt_ini_input" not in st.session_state:
    st.session_state["macro_dt_ini_input"] = st.session_state["macro_dt_ini_value"]
if "macro_dt_fim_input" not in st.session_state:
    st.session_state["macro_dt_fim_input"] = st.session_state["macro_dt_fim_value"]

snapshot_active = SNAPSHOT_BR_CSV_PATH.exists() or SNAPSHOT_BR_PATH.exists()
if snapshot_active:
    full_df_long, full_by_key = load_macro_snapshot_panel(DATA_PIPELINE_VERSION, snapshot_mtime)
else:
    full_df_long, full_by_key = pd.DataFrame(columns=["data", "valor", "key"]), {}


col_group, col_ind, col_period, col_start, col_end = st.columns([1, 1, 1, 1, 1], gap="small")

with col_group:
    st.markdown('<div class="filter-label">Grupo</div>', unsafe_allow_html=True)
    selected_group = st.selectbox("Grupo", groups, key="macro_group", label_visibility="collapsed")

group_catalog = catalog[catalog["grupo"] == selected_group].copy()
valid_keys_for_group = list(group_catalog["key"])
previous_group = st.session_state.get("macro_group_last_applied")
if previous_group != selected_group:
    st.session_state["macro_selected_keys"] = valid_keys_for_group.copy()
    st.session_state["macro_group_last_applied"] = selected_group

current_selected = [key for key in st.session_state.get("macro_selected_keys", []) if key in valid_keys_for_group]
st.session_state["macro_selected_keys"] = current_selected

label_map = {row["key"]: compact_label(row) for _, row in group_catalog.iterrows()}
for key in valid_keys_for_group:
    checkbox_state_key = f"macro_check_{key}"
    if previous_group != selected_group or checkbox_state_key not in st.session_state:
        st.session_state[checkbox_state_key] = key in current_selected

with col_ind:
    st.markdown('<div class="filter-label">Indicadores</div>', unsafe_allow_html=True)
    selected_keys = render_indicator_picker("macro", valid_keys_for_group, label_map)

if not selected_keys:
    st.info("Selecione ao menos um indicador para visualizar os dados.")
    st.stop()

expanded_selected_keys = expand_indicator_keys(selected_keys)
selected_has_derived = any(key in DERIVED_DEPENDENCIES for key in selected_keys)

with col_period:
    st.markdown('<div class="filter-label">Per&iacute;odo</div>', unsafe_allow_html=True)
    period = st.selectbox("Periodo", PERIOD_OPTIONS, key="macro_period", label_visibility="collapsed")

if snapshot_active:
    snapshot_subset = {
        str(key): full_by_key.get(str(key), pd.DataFrame(columns=["data", "valor"])).copy()
        for key in expanded_selected_keys
    }
    snapshot_subset = recompute_visual_derived_series(snapshot_subset)
    available_df = build_available_frame(snapshot_subset, selected_keys)
else:
    _, full_by_key = load_macro_live_subset_data(
        tuple(expanded_selected_keys),
        None,
        None,
        DATA_PIPELINE_VERSION,
        codes_mtime,
    )
    available_df = build_available_frame(full_by_key, selected_keys)

available_ranges_df = indicator_available_ranges(available_df)
selected_range_rows = available_ranges_df[available_ranges_df["key"].isin(selected_keys)].copy()
if selected_range_rows.empty:
    global_min = pd.Timestamp("1960-01-01").normalize()
    global_max = pd.Timestamp.today().normalize()
else:
    global_min = selected_range_rows["data_min"].min().normalize()
    global_max = selected_range_rows["data_max"].max().normalize()

signature = (selected_group, tuple(selected_keys), period)
if st.session_state.get("macro_period_signature") != signature:
    preset_ini, preset_fim = preset_dates(period, global_min, global_max)
    st.session_state["macro_dt_ini_value"] = preset_ini.date()
    st.session_state["macro_dt_fim_value"] = preset_fim.date()
    st.session_state["macro_dt_ini_input"] = preset_ini.date()
    st.session_state["macro_dt_fim_input"] = preset_fim.date()
    st.session_state["macro_period_signature"] = signature

with col_start:
    st.markdown('<div class="filter-label">In&iacute;cio</div>', unsafe_allow_html=True)
    dt_ini_value = st.date_input(
        "Início",
        min_value=global_min.date(),
        max_value=global_max.date(),
        key="macro_dt_ini_input",
        format="YYYY/MM/DD",
        label_visibility="collapsed",
    )

with col_end:
    st.markdown('<div class="filter-label">Fim</div>', unsafe_allow_html=True)
    dt_fim_value = st.date_input(
        "Fim",
        min_value=global_min.date(),
        max_value=global_max.date(),
        key="macro_dt_fim_input",
        format="YYYY/MM/DD",
        label_visibility="collapsed",
    )

row_a, row_b, row_c, row_d, row_e = st.columns(5, gap="medium")
with row_a:
    st.markdown('<div class="filter-action filter-row-bottom"></div>', unsafe_allow_html=True)
    compare_base100 = st.checkbox("Comparar (base 100)", key="macro_compare_base100")
with row_b:
    st.markdown("", unsafe_allow_html=True)
with row_c:
    st.markdown("", unsafe_allow_html=True)
with row_d:
    st.markdown("", unsafe_allow_html=True)
with row_e:
    st.markdown("", unsafe_allow_html=True)

dt_ini, dt_fim = clamp_date_range(
    pd.Timestamp(dt_ini_value),
    pd.Timestamp(dt_fim_value),
    global_min,
    global_max,
)

if dt_ini.date() != st.session_state["macro_dt_ini_value"] or dt_fim.date() != st.session_state["macro_dt_fim_value"]:
    st.session_state["macro_dt_ini_value"] = dt_ini.date()
    st.session_state["macro_dt_fim_value"] = dt_fim.date()
    st.rerun()

if snapshot_active:
    by_key = {
        str(key): full_by_key.get(str(key), pd.DataFrame(columns=["data", "valor"])).copy()
        for key in expanded_selected_keys
    }
    by_key = recompute_visual_derived_series(by_key)
    df_long = filter_long_frame_by_date(full_df_long, selected_keys, dt_ini, dt_fim)
else:
    df_long, by_key = load_macro_live_subset_data(
        tuple(expanded_selected_keys),
        dt_ini.strftime("%Y-%m-%d"),
        dt_fim.strftime("%Y-%m-%d"),
        DATA_PIPELINE_VERSION,
        codes_mtime,
    )

if selected_has_derived:
    by_key = recompute_visual_derived_series(by_key)

available_min = global_min
available_max = global_max

st.markdown(
    f'<p class="range-note">Dados disponíveis para a seleção atual: {format_br_date(available_min)} a {format_br_date(available_max)}.</p>',
    unsafe_allow_html=True,
)


selected_meta = catalog[catalog["key"].isin(selected_keys)].copy()
selected_meta = selected_meta.set_index("key").loc[selected_keys].reset_index()

for idx in range(0, len(selected_keys), 2):
    row_keys = selected_keys[idx : idx + 2]
    cols = st.columns(2, gap="large")

    for col_idx, key in enumerate(row_keys):
        meta = meta_by_key.loc[key]
        if key == "pib_efetivo_potencial_hiato":
            serie, serie_resolved, alert_message = resolve_hiato_series(
                dt_ini,
                dt_fim,
                codes_mtime,
                DATA_PIPELINE_VERSION,
            )
        else:
            serie = by_key.get(key, pd.DataFrame(columns=["data", "valor"])).copy()
            if serie.empty and snapshot_active:
                serie = full_by_key.get(str(key), pd.DataFrame(columns=["data", "valor"])).copy()
            serie = clean_indicator_series(serie)
            if serie.empty:
                serie = clean_indicator_series(load_live_fallback_series(key, dt_ini, dt_fim, codes_mtime, DATA_PIPELINE_VERSION))

            serie_resolved, alert_message = resolve_indicator_window(
                serie,
                str(meta.get("periodicidade", "")),
                dt_ini,
                dt_fim,
                "Mais proximo disponivel",
            )

        ipca_special, m1_special = build_special_comparison_df(key, by_key)
        ipca_special_resolved = pd.DataFrame()
        m1_special_resolved = pd.DataFrame()
        if not ipca_special.empty:
            ipca_dt_ini = dt_ini - pd.DateOffset(months=LEAD_MESES_M1)
            ipca_dt_fim = dt_fim - pd.DateOffset(months=LEAD_MESES_M1)
            ipca_special_resolved = ipca_special[
                (ipca_special["data"] >= ipca_dt_ini) & (ipca_special["data"] <= ipca_dt_fim)
            ].copy()
        if not m1_special.empty:
            m1_special_resolved = m1_special[
                (m1_special["data"] >= dt_ini) & (m1_special["data"] <= dt_fim)
            ].copy()

        if compare_base100 and not serie_resolved.empty and key != "pib_efetivo_potencial_hiato":
            serie_resolved = normalize_base_100(serie_resolved)

        chart_type = str(meta.get("tipo_grafico", "linhas"))
        indicator_name = fix_mojibake(str(meta.get("indicador") or meta.get("nome") or key))
        unit_label = "Base 100" if compare_base100 else fix_mojibake(str(meta.get("unidade") or ""))
        if key == "inflacao12_m1yoy" and (not ipca_special.empty or not m1_special.empty):
            frames = [df for df in (ipca_special, m1_special) if not df.empty]
            display_source = pd.concat(frames, ignore_index=True) if frames else serie
        else:
            display_source = serie
        if key == "pib_efetivo_potencial_hiato" and not serie_resolved.empty:
            display_source = serie_resolved
        available_min = format_br_date(display_source["data"].min()) if not display_source.empty else "-"
        available_max = format_br_date(display_source["data"].max()) if not display_source.empty else "-"
        periodicidade = fix_mojibake(str(meta.get("periodicidade") or ""))
        if key == "pib_efetivo_potencial_hiato":
            periodicidade = "mensal"
        with cols[col_idx]:
            metric_source = ipca_special_resolved if key == "inflacao12_m1yoy" and not ipca_special_resolved.empty else serie_resolved
            latest_valid = metric_source.dropna(subset=["valor"]).sort_values("data")
            if latest_valid.empty:
                value_html = "-"
                date_html = "Ultima data: -"
                pill_html = '<span class="metric-pill metric-neutral">Sem variacao</span>'
                metric_label = "Ultimo valor"
            else:
                last_row = latest_valid.iloc[-1]
                value_html = format_br_number(last_row["valor"], CASAS)
                date_html = f"Ultima data: {format_br_date(last_row['data'])}"
                delta_abs, delta_pct, delta_css = metric_delta_parts(latest_valid)
                pill_html = ""
                if delta_abs:
                    pill_html += f'<span class="metric-pill {delta_css}">{delta_abs}</span>'
                if delta_pct:
                    pill_html += f'<span class="metric-pill {delta_css}">{delta_pct}</span>'
                if not pill_html:
                    pill_html = '<span class="metric-pill metric-neutral">Sem variacao</span>'
                if key == "inflacao12_m1yoy":
                    metric_label = "Ultimo IPCA 12m"
                elif key == "pib_efetivo_potencial_hiato":
                    metric_label = "Ultimo hiato"
                else:
                    metric_label = "Ultimo valor"

            st.markdown(
                f"""
                <div class="chart-head">
                    <div class="chart-copy">
                        <div class="chart-title">{indicator_name}</div>
                        <p class="chart-subtitle">Disponivel de {available_min} a {available_max} - Frequencia: {periodicidade}</p>
                    </div>
                    <div class="metric-wrap">
                        <p class="metric-label">{metric_label}</p>
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

            if key == "inflacao12_m1yoy":
                if ipca_special_resolved.empty and m1_special_resolved.empty:
                    st.markdown('<div class="inline-alert">Sem dados disponiveis para este indicador.</div>', unsafe_allow_html=True)
                    continue
            elif serie_resolved.empty:
                st.markdown('<div class="inline-alert">Sem dados disponiveis para este indicador.</div>', unsafe_allow_html=True)
                continue

            if key == "inflacao12_m1yoy":
                fig = build_inflation_vs_m1_chart(
                    ipca_special_resolved,
                    m1_special_resolved,
                )
            elif key == "pib_efetivo_potencial_hiato":
                fig = build_pib_effective_potential_gap_chart(serie_resolved)
            else:
                fig = build_indicator_chart(serie_resolved, chart_type, unit_label, series_key=key)
            st.plotly_chart(
                fig,
                width="stretch",
                config={"displaylogo": False, "modeBarButtonsToRemove": ["toggleSpikelines"], "responsive": True},
            )

