# -*- coding: utf-8 -*-
import io

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _make_session() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def dados_tesouro(url: str) -> pd.DataFrame:
    session = _make_session()
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        content = response.content.decode("latin1")
    finally:
        session.close()

    df = pd.read_csv(io.StringIO(content), sep=";", decimal=",")
    df["Data Vencimento"] = pd.to_datetime(df["Data Vencimento"], format="%d/%m/%Y", errors="coerce")
    df["Data Base"] = pd.to_datetime(df["Data Base"], format="%d/%m/%Y", errors="coerce")
    return df
