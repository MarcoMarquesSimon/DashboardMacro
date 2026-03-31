# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd
from fredapi import Fred


FRED_INDICATORS = [
    {
        "id": "CPIAUCSL",
        "key": "cpi",
        "indicador": "CPI",
        "descricao": "Índice de Preços ao Consumidor (inflação cheia)",
        "frequencia": "mensal",
        "grupo": "Inflação",
        "unidade": "índice",
        "tipo_grafico": "linhas",
    },
    {
        "id": "PCUOMFGOMFG",
        "key": "ppi",
        "indicador": "PPI",
        "descricao": "Índice de Preços ao Produtor",
        "frequencia": "mensal",
        "grupo": "Inflação",
        "unidade": "índice",
        "tipo_grafico": "linhas",
    },
    {
        "id": "DPCCRV1Q225SBEA",
        "key": "core_pce",
        "indicador": "Core PCE",
        "descricao": "Inflação Core PCE, medida preferida do Fed",
        "frequencia": "trimestral",
        "grupo": "Inflação",
        "unidade": "%",
        "tipo_grafico": "linhas",
    },
    {
        "id": "FEDFUNDS",
        "key": "fed_funds",
        "indicador": "Fed Funds Rate",
        "descricao": "Taxa básica de juros dos Estados Unidos",
        "frequencia": "mensal",
        "grupo": "Juros",
        "unidade": "%",
        "tipo_grafico": "linhas",
    },
    {
        "id": "DGS10",
        "key": "treasury_10y",
        "indicador": "10Y Treasury",
        "descricao": "Taxa do Treasury de 10 anos",
        "frequencia": "diária",
        "grupo": "Juros",
        "unidade": "%",
        "tipo_grafico": "linhas",
    },
    {
        "id": "DGS2",
        "key": "treasury_2y",
        "indicador": "2Y Treasury",
        "descricao": "Taxa do Treasury de 2 anos",
        "frequencia": "diária",
        "grupo": "Juros",
        "unidade": "%",
        "tipo_grafico": "linhas",
    },
    {
        "id": "T10Y2Y",
        "key": "yield_curve_10y_2y",
        "indicador": "Yield Curve (10Y-2Y)",
        "descricao": "Spread entre Treasuries de 10 anos e 2 anos",
        "frequencia": "diária",
        "grupo": "Juros",
        "unidade": "p.p.",
        "tipo_grafico": "linhas",
    },
    {
        "id": "UNRATE",
        "key": "unemployment_rate",
        "indicador": "Unemployment Rate",
        "descricao": "Taxa de desemprego dos Estados Unidos",
        "frequencia": "mensal",
        "grupo": "Trabalho",
        "unidade": "%",
        "tipo_grafico": "linhas",
    },
    {
        "id": "PAYEMS",
        "key": "nonfarm_payrolls",
        "indicador": "Nonfarm Payrolls",
        "descricao": "Total de empregos não agrícolas",
        "frequencia": "mensal",
        "grupo": "Trabalho",
        "unidade": "mil",
        "tipo_grafico": "linhas",
    },
    {
        "id": "GDP",
        "key": "gdp_nominal",
        "indicador": "GDP",
        "descricao": "Produto Interno Bruto nominal",
        "frequencia": "trimestral",
        "grupo": "Atividade",
        "unidade": "US$ bilhões",
        "tipo_grafico": "linhas",
    },
    {
        "id": "GDPC1",
        "key": "gdp_real",
        "indicador": "Real GDP",
        "descricao": "Produto Interno Bruto real",
        "frequencia": "trimestral",
        "grupo": "Atividade",
        "unidade": "US$ bilhões",
        "tipo_grafico": "linhas",
    },
    {
        "id": "INDPRO",
        "key": "industrial_production",
        "indicador": "Industrial Production",
        "descricao": "Produção industrial dos Estados Unidos",
        "frequencia": "mensal",
        "grupo": "Atividade",
        "unidade": "índice",
        "tipo_grafico": "linhas",
    },
    {
        "id": "HOUST",
        "key": "housing_starts",
        "indicador": "Housing Starts",
        "descricao": "Novas construções residenciais",
        "frequencia": "mensal",
        "grupo": "Atividade",
        "unidade": "mil",
        "tipo_grafico": "linhas",
    },
    {
        "id": "RSAFS",
        "key": "retail_sales",
        "indicador": "Retail Sales",
        "descricao": "Vendas no varejo",
        "frequencia": "mensal",
        "grupo": "Consumo",
        "unidade": "US$ milhões",
        "tipo_grafico": "linhas",
    },
    {
        "id": "UMCSENT",
        "key": "consumer_sentiment",
        "indicador": "Consumer Sentiment",
        "descricao": "Índice de sentimento do consumidor",
        "frequencia": "mensal",
        "grupo": "Sentimento",
        "unidade": "índice",
        "tipo_grafico": "linhas",
    },
    {
        "id": "M2SL",
        "key": "money_supply_m2",
        "indicador": "Money Supply M2",
        "descricao": "Oferta monetária M2",
        "frequencia": "mensal",
        "grupo": "Liquidez",
        "unidade": "US$ bilhões",
        "tipo_grafico": "linhas",
    },
    {
        "id": "DTWEXBGS",
        "key": "dollar_index",
        "indicador": "Dollar Index",
        "descricao": "Índice do dólar ponderado pelo comércio",
        "frequencia": "diária",
        "grupo": "Câmbio",
        "unidade": "índice",
        "tipo_grafico": "linhas",
    },
]


def get_fred_catalog() -> pd.DataFrame:
    catalog = pd.DataFrame(FRED_INDICATORS)
    catalog["ordem"] = 1
    return catalog


def get_fred_data(api_key: str) -> Dict[str, pd.DataFrame]:
    fred = Fred(api_key=api_key)
    dfs_dict: Dict[str, pd.DataFrame] = {}

    for meta in FRED_INDICATORS:
        series = fred.get_series(meta["id"])
        df = pd.DataFrame({"data": pd.to_datetime(series.index), "valor": pd.to_numeric(series.values, errors="coerce")})
        df = df.dropna(subset=["data", "valor"]).sort_values("data").reset_index(drop=True)
        dfs_dict[meta["id"]] = df

    return dfs_dict


def fetch_all_fred_indicators(api_key: str) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], pd.DataFrame]:
    catalog = get_fred_catalog()
    raw_dict = get_fred_data(api_key)

    rows = []
    by_key: Dict[str, pd.DataFrame] = {}
    for _, meta in catalog.iterrows():
        series_id = str(meta["id"])
        key = str(meta["key"])
        serie = raw_dict.get(series_id, pd.DataFrame(columns=["data", "valor"])).copy()
        by_key[key] = serie.copy()

        if serie.empty:
            continue

        tmp = serie.copy()
        for col in catalog.columns:
            tmp[col] = meta[col]
        rows.append(tmp)

    if rows:
        df_long = pd.concat(rows, ignore_index=True)
        df_long = df_long.sort_values(["key", "data"]).reset_index(drop=True)
    else:
        df_long = pd.DataFrame(columns=["data", "valor", *catalog.columns.tolist()])

    return df_long, by_key, catalog
