# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


FRED_SERIES_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_SERIES_META_URL = "https://api.stlouisfed.org/fred/series"

FRED_INDICATORS = [
    {"id": "CPIAUCSL", "key": "cpi", "indicador": "CPI", "descricao": "Indice de Precos ao Consumidor (inflacao cheia)", "frequencia": "mensal", "grupo": "Inflacao", "unidade": "indice", "tipo_grafico": "linhas"},
    {"id": "PCUOMFGOMFG", "key": "ppi", "indicador": "PPI", "descricao": "Indice de Precos ao Produtor", "frequencia": "mensal", "grupo": "Inflacao", "unidade": "indice", "tipo_grafico": "linhas"},
    {"id": "DPCCRV1Q225SBEA", "key": "core_pce", "indicador": "Core PCE", "descricao": "Inflacao Core PCE, medida preferida do Fed", "frequencia": "trimestral", "grupo": "Inflacao", "unidade": "%", "tipo_grafico": "linhas"},
    {"id": "PCETRIM1M158SFRBDAL", "key": "trimmed_mean_pce_1m", "indicador": "Trimmed Mean PCE (1m)", "descricao": "Trimmed Mean PCE Inflation Rate (1-month annualized)", "frequencia": "mensal", "grupo": "Inflacao", "unidade": "%", "tipo_grafico": "linhas"},
    {"id": "FEDFUNDS", "key": "fed_funds", "indicador": "Fed Funds Rate", "descricao": "Taxa basica de juros dos Estados Unidos", "frequencia": "mensal", "grupo": "Juros", "unidade": "%", "tipo_grafico": "linhas"},
    {"id": "DGS10", "key": "treasury_10y", "indicador": "10Y Treasury", "descricao": "Taxa do Treasury de 10 anos", "frequencia": "diaria", "grupo": "Juros", "unidade": "%", "tipo_grafico": "linhas"},
    {"id": "DGS2", "key": "treasury_2y", "indicador": "2Y Treasury", "descricao": "Taxa do Treasury de 2 anos", "frequencia": "diaria", "grupo": "Juros", "unidade": "%", "tipo_grafico": "linhas"},
    {"id": "T10Y2Y", "key": "yield_curve_10y_2y", "indicador": "Yield Curve (10Y-2Y)", "descricao": "Spread entre Treasuries de 10 anos e 2 anos", "frequencia": "diaria", "grupo": "Juros", "unidade": "p.p.", "tipo_grafico": "linhas"},
    {"id": "UNRATE", "key": "unemployment_rate", "indicador": "Unemployment Rate", "descricao": "Taxa de desemprego dos Estados Unidos", "frequencia": "mensal", "grupo": "Trabalho", "unidade": "%", "tipo_grafico": "linhas"},
    {"id": "PAYEMS", "key": "nonfarm_payrolls", "indicador": "Nonfarm Payrolls", "descricao": "Total de empregos nao agricolas", "frequencia": "mensal", "grupo": "Trabalho", "unidade": "mil", "tipo_grafico": "linhas"},
    {"id": "GDP", "key": "gdp_nominal", "indicador": "GDP", "descricao": "Produto Interno Bruto nominal", "frequencia": "trimestral", "grupo": "Atividade", "unidade": "US$ bilhoes", "tipo_grafico": "linhas"},
    {"id": "GDPC1", "key": "gdp_real", "indicador": "Real GDP", "descricao": "Produto Interno Bruto real", "frequencia": "trimestral", "grupo": "Atividade", "unidade": "US$ bilhoes", "tipo_grafico": "linhas"},
    {"id": "INDPRO", "key": "industrial_production", "indicador": "Industrial Production", "descricao": "Producao industrial dos Estados Unidos", "frequencia": "mensal", "grupo": "Atividade", "unidade": "indice", "tipo_grafico": "linhas"},
    {"id": "HOUST", "key": "housing_starts", "indicador": "Housing Starts", "descricao": "Novas construcoes residenciais", "frequencia": "mensal", "grupo": "Atividade", "unidade": "mil", "tipo_grafico": "linhas"},
    {"id": "RSAFS", "key": "retail_sales", "indicador": "Retail Sales", "descricao": "Vendas no varejo", "frequencia": "mensal", "grupo": "Consumo", "unidade": "US$ milhoes", "tipo_grafico": "linhas"},
    {"id": "UMCSENT", "key": "consumer_sentiment", "indicador": "Consumer Sentiment", "descricao": "Indice de sentimento do consumidor", "frequencia": "mensal", "grupo": "Sentimento", "unidade": "indice", "tipo_grafico": "linhas"},
    {"id": "M2SL", "key": "money_supply_m2", "indicador": "Money Supply M2", "descricao": "Oferta monetaria M2", "frequencia": "mensal", "grupo": "Liquidez", "unidade": "US$ bilhoes", "tipo_grafico": "linhas"},
    {"id": "DTWEXBGS", "key": "dollar_index", "indicador": "Dollar Index", "descricao": "Indice do dolar ponderado pelo comercio", "frequencia": "diaria", "grupo": "Cambio", "unidade": "indice", "tipo_grafico": "linhas"},
]


def _make_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "DashboardMacro/1.0", "Accept": "application/json"})
    return session


def get_fred_catalog() -> pd.DataFrame:
    catalog = pd.DataFrame(FRED_INDICATORS)
    catalog["ordem"] = 1
    return catalog


def _fetch_one_series(session: requests.Session, series_id: str, api_key: str, timeout: int = 30) -> pd.DataFrame:
    response = session.get(
        FRED_SERIES_URL,
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "asc",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    observations = payload.get("observations", [])
    if not observations:
        return pd.DataFrame(columns=["data", "valor"])

    df = pd.DataFrame(observations)
    if "date" not in df.columns or "value" not in df.columns:
        return pd.DataFrame(columns=["data", "valor"])

    out = pd.DataFrame(
        {
            "data": pd.to_datetime(df["date"], errors="coerce"),
            "valor": pd.to_numeric(df["value"].replace(".", pd.NA), errors="coerce"),
        }
    )
    out = out.dropna(subset=["data", "valor"]).sort_values("data").reset_index(drop=True)
    return out


def _fetch_one_series_with_params(
    session: requests.Session,
    series_id: str,
    api_key: str,
    *,
    frequency: str | None = None,
    aggregation_method: str | None = None,
    timeout: int = 30,
) -> pd.DataFrame:
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "asc",
    }
    if frequency:
        params["frequency"] = frequency
    if aggregation_method:
        params["aggregation_method"] = aggregation_method

    response = session.get(FRED_SERIES_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    observations = payload.get("observations", [])
    if not observations:
        return pd.DataFrame(columns=["data", "valor"])

    df = pd.DataFrame(observations)
    if "date" not in df.columns or "value" not in df.columns:
        return pd.DataFrame(columns=["data", "valor"])

    out = pd.DataFrame(
        {
            "data": pd.to_datetime(df["date"], errors="coerce"),
            "valor": pd.to_numeric(df["value"].replace(".", pd.NA), errors="coerce"),
        }
    )
    out = out.dropna(subset=["data", "valor"]).sort_values("data").reset_index(drop=True)
    return out


def fetch_series_variant(
    api_key: str,
    series_id: str,
    *,
    frequency: str | None = None,
    aggregation_method: str = "avg",
) -> pd.DataFrame:
    session = _make_session()
    try:
        return _fetch_one_series_with_params(
            session,
            series_id,
            api_key,
            frequency=frequency,
            aggregation_method=aggregation_method if frequency else None,
        )
    finally:
        session.close()


def _fetch_series_metadata(session: requests.Session, series_id: str, api_key: str, timeout: int = 30) -> dict:
    response = session.get(
        FRED_SERIES_META_URL,
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    series_list = payload.get("seriess", [])
    if not series_list:
        return {}
    return dict(series_list[0])


def _normalize_fred_frequency(meta: dict, fallback: str) -> str:
    freq = str(meta.get("frequency_short") or meta.get("frequency") or fallback or "").strip().lower()
    mapping = {
        "d": "diaria",
        "w": "semanal",
        "bw": "quinzenal",
        "m": "mensal",
        "q": "trimestral",
        "sa": "semestral",
        "a": "anual",
        "daily": "diaria",
        "weekly": "semanal",
        "biweekly": "quinzenal",
        "monthly": "mensal",
        "quarterly": "trimestral",
        "semiannual": "semestral",
        "annual": "anual",
    }
    return mapping.get(freq, freq or str(fallback or "").strip().lower())


def get_fred_data(api_key: str) -> Dict[str, pd.DataFrame]:
    session = _make_session()
    dfs_dict: Dict[str, pd.DataFrame] = {}
    meta_dict: Dict[str, dict] = {}
    try:
        for meta in FRED_INDICATORS:
            series_id = str(meta["id"])
            try:
                dfs_dict[series_id] = _fetch_one_series(session, series_id, api_key=api_key)
            except Exception:
                dfs_dict[series_id] = pd.DataFrame(columns=["data", "valor"])
            try:
                meta_dict[series_id] = _fetch_series_metadata(session, series_id, api_key=api_key)
            except Exception:
                meta_dict[series_id] = {}
    finally:
        session.close()
    return dfs_dict, meta_dict


def fetch_all_fred_indicators(api_key: str) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], pd.DataFrame]:
    catalog = get_fred_catalog()
    raw_dict, raw_meta_dict = get_fred_data(api_key)

    rows = []
    by_key: Dict[str, pd.DataFrame] = {}
    for _, meta in catalog.iterrows():
        series_id = str(meta["id"])
        key = str(meta["key"])
        serie = raw_dict.get(series_id, pd.DataFrame(columns=["data", "valor"])).copy()
        by_key[key] = serie.copy()
        serie_meta = raw_meta_dict.get(series_id, {})
        resolved_freq = _normalize_fred_frequency(serie_meta, str(meta.get("frequencia", "")))

        if serie.empty:
            continue

        tmp = serie.copy()
        for col in catalog.columns:
            tmp[col] = meta[col]
        tmp["frequencia"] = resolved_freq
        rows.append(tmp)

    if rows:
        df_long = pd.concat(rows, ignore_index=True)
        df_long = df_long.sort_values(["key", "data"]).reset_index(drop=True)
    else:
        df_long = pd.DataFrame(columns=["data", "valor", *catalog.columns.tolist()])

    if not df_long.empty:
        freq_map = (
            df_long[["key", "frequencia"]]
            .dropna(subset=["key", "frequencia"])
            .drop_duplicates(subset=["key"], keep="last")
        )
        if not freq_map.empty:
            catalog = catalog.merge(freq_map, on="key", how="left", suffixes=("", "_api"))
            catalog["frequencia"] = catalog["frequencia_api"].fillna(catalog["frequencia"])
            catalog = catalog.drop(columns=["frequencia_api"])

    return df_long, by_key, catalog
