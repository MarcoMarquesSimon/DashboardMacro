# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import quote

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BCB_SGS_JSON = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?formato=json"
BCB_SGS_CSV = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?formato=csv"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DashboardMacro/1.0)",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

EMPTY_COLUMNS = ["data", "valor"]
MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ð", "\x8d", "\x81", "\x82", "\x83")


def _empty_df(**attrs: Any) -> pd.DataFrame:
    df = pd.DataFrame(columns=EMPTY_COLUMNS)
    df.attrs.update(
        {
            "code": None,
            "requested_start": None,
            "requested_end": None,
            "source": "empty",
            "used_full_series_fallback": False,
            "missing_values": 0,
            "last_valid_date": None,
            "last_valid_value": None,
            "message": "",
        }
    )
    df.attrs.update(attrs)
    return df


def _fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return text

    original = text.replace("\ufeff", "").strip()
    if not any(marker in original for marker in MOJIBAKE_MARKERS):
        return original.replace("\u00a0", " ").strip()

    current = original
    for _ in range(2):
        try:
            repaired = current.encode("latin1").decode("utf-8")
        except Exception:
            break
        if repaired == current:
            break
        current = repaired

    normalized = current.replace("\u00a0", " ").replace("\ufeff", "").strip()
    return unicodedata.normalize("NFC", normalized)


def _clean_text_series(series: pd.Series) -> pd.Series:
    return series.map(lambda value: _fix_mojibake(value) if pd.notna(value) else value)


def _normalize_date_param(value: Any) -> str | None:
    if value in (None, ""):
        return None

    ts = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Data invalida: {value!r}. Use um formato como '01/01/2020'.")

    return ts.strftime("%d/%m/%Y")


def _build_url(code: int, formato: str, inicio: str | None = None, fim: str | None = None) -> str:
    base = (BCB_SGS_JSON if formato == "json" else BCB_SGS_CSV).format(code=int(code))
    params = []
    if inicio:
        params.append(f"dataInicial={quote(inicio)}")
    if fim:
        params.append(f"dataFinal={quote(fim)}")
    if params:
        return f"{base}&{'&'.join(params)}"
    return base


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
    session.headers.update(DEFAULT_HEADERS)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    return out


def _parse_valor_series(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = s.str.replace("\u00a0", "", regex=False)
    s = s.str.replace(" ", "", regex=False)

    has_comma = s.str.contains(",", na=False)
    s = s.where(~has_comma, s.str.replace(".", "", regex=False))
    s = s.where(~has_comma, s.str.replace(",", ".", regex=False))

    return pd.to_numeric(s, errors="coerce")


def _parse_sgs_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return _empty_df()

    df = _standardize_columns(df)
    if "data" not in df.columns or "valor" not in df.columns:
        return _empty_df(message="Resposta da API sem colunas 'data' e 'valor'.")

    parsed = pd.DataFrame(
        {
            "data": pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce"),
            "valor": _parse_valor_series(df["valor"]),
        }
    )
    parsed = parsed.dropna(subset=["data"]).drop_duplicates(subset=["data"]).sort_values("data").reset_index(drop=True)
    return parsed


def _read_csv_flexible(text: str) -> pd.DataFrame:
    text = text.strip()
    if not text:
        return _empty_df()

    for sep in (";", ","):
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep)
            cols = {str(c).strip().lower() for c in df.columns}
            if {"data", "valor"}.issubset(cols):
                return df
        except Exception:
            continue

    try:
        return pd.read_csv(io.StringIO(text), sep=None, engine="python")
    except Exception:
        return _empty_df(message="Nao foi possivel interpretar o CSV retornado pelo SGS.")


def _apply_metadata(df: pd.DataFrame, **attrs: Any) -> pd.DataFrame:
    out = df.copy()
    valid = out.dropna(subset=["valor"])
    base_attrs = {
        "missing_values": int(out["valor"].isna().sum()) if "valor" in out.columns else 0,
        "last_valid_date": valid["data"].max() if not valid.empty else None,
        "last_valid_value": valid.iloc[-1]["valor"] if not valid.empty else None,
    }
    out.attrs.update(base_attrs)
    out.attrs.update(attrs)
    return out


def _extract_error_payload(response: requests.Response) -> tuple[str, str]:
    try:
        payload = response.json()
    except ValueError:
        return "", ""

    if isinstance(payload, dict):
        error = str(payload.get("error") or "").strip()
        message = str(payload.get("message") or "").strip()
        return error, message
    return "", ""


def _extract_error_message(response: requests.Response) -> str:
    error, message = _extract_error_payload(response)
    return message or error


def _is_daily_window_error(response: requests.Response) -> bool:
    error, message = _extract_error_payload(response)
    combined = f"{error} {message}".lower()
    return "10 anos" in combined and "periodicidade diária" in combined


def _parse_json_payload(response: requests.Response) -> pd.DataFrame:
    try:
        payload = response.json()
    except ValueError:
        return _empty_df(message="Resposta JSON invalida da API do SGS.")

    if isinstance(payload, dict):
        message = str(payload.get("message") or payload.get("error") or "").strip()
        return _empty_df(message=message or "Resposta JSON invalida da API do SGS.")

    return _parse_sgs_df(pd.DataFrame(payload))


def _chunk_daily_series(
    session: requests.Session,
    code: int,
    timeout: int,
    inicio: str | None = None,
    fim: str | None = None,
) -> pd.DataFrame:
    end_ts = pd.to_datetime(fim, dayfirst=True) if fim else pd.Timestamp.today().normalize()
    start_ts = pd.to_datetime(inicio, dayfirst=True) if inicio else pd.Timestamp("1900-01-01")

    if start_ts > end_ts:
        return _empty_df(message="Serie sem dados para o intervalo solicitado.")

    parts = []
    cursor = start_ts
    while cursor <= end_ts:
        chunk_end = min(cursor + pd.DateOffset(years=10) - pd.Timedelta(days=1), end_ts)
        chunk_df = _request_series(
            session,
            code,
            timeout=timeout,
            inicio=cursor.strftime("%d/%m/%Y"),
            fim=chunk_end.strftime("%d/%m/%Y"),
        )
        if not chunk_df.empty:
            parts.append(chunk_df)
        cursor = chunk_end + pd.Timedelta(days=1)

    if not parts:
        return _empty_df(message="Serie diaria sem dados nos blocos consultados.")

    out = pd.concat(parts, ignore_index=True)
    out = out.drop_duplicates(subset=["data"]).sort_values("data").reset_index(drop=True)
    return out


def _request_series(
    session: requests.Session,
    code: int,
    timeout: int,
    inicio: str | None = None,
    fim: str | None = None,
) -> pd.DataFrame:
    url_json = _build_url(code, "json", inicio=inicio, fim=fim)
    response = session.get(url_json, timeout=timeout)

    if response.status_code in (204, 404):
        return _empty_df(message="Serie sem dados para o intervalo solicitado.")

    if response.status_code == 406 and _is_daily_window_error(response):
        return _chunk_daily_series(session, code, timeout=timeout, inicio=inicio, fim=fim)

    if response.status_code == 406:
        url_csv = _build_url(code, "csv", inicio=inicio, fim=fim)
        response = session.get(
            url_csv,
            headers={**DEFAULT_HEADERS, "Accept": "text/csv,*/*"},
            timeout=timeout,
        )
        if response.status_code in (204, 404):
            return _empty_df(message="Serie sem dados para o intervalo solicitado.")
        if response.status_code == 406 and _is_daily_window_error(response):
            return _chunk_daily_series(session, code, timeout=timeout, inicio=inicio, fim=fim)
        response.raise_for_status()
        if "application/json" in str(response.headers.get("content-type", "")).lower():
            return _parse_json_payload(response)
        return _parse_sgs_df(_read_csv_flexible(response.text))

    response.raise_for_status()
    return _parse_json_payload(response)


def _filter_date_range(df: pd.DataFrame, inicio: str | None, fim: str | None) -> pd.DataFrame:
    out = df.copy()
    if inicio:
        out = out[out["data"] >= pd.to_datetime(inicio, dayfirst=True)]
    if fim:
        out = out[out["data"] <= pd.to_datetime(fim, dayfirst=True)]
    return out.reset_index(drop=True)


def _cache_paths(cache_dir: Path, code: int) -> tuple[Path, Path]:
    return cache_dir / f"sgs_{int(code)}.parquet", cache_dir / f"sgs_{int(code)}.pkl"


def _cache_is_fresh(path: Path, ttl_hours: int | None) -> bool:
    if not path.exists() or ttl_hours is None:
        return False
    age_hours = ((pd.Timestamp.now() - pd.Timestamp(path.stat().st_mtime, unit="s")).total_seconds() / 3600)
    return age_hours <= ttl_hours


def _read_cache(cache_dir: Path, code: int, ttl_hours: int | None) -> pd.DataFrame | None:
    parquet_path, pickle_path = _cache_paths(cache_dir, code)

    for path, reader in ((parquet_path, pd.read_parquet), (pickle_path, pd.read_pickle)):
        if not _cache_is_fresh(path, ttl_hours):
            continue
        try:
            df = reader(path)
            if {"data", "valor"}.issubset(df.columns):
                df["data"] = pd.to_datetime(df["data"], errors="coerce")
                df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
                df = df.dropna(subset=["data"]).sort_values("data").reset_index(drop=True)
                return _apply_metadata(df, source=f"cache:{path.suffix.lstrip('.')}")
        except Exception:
            continue
    return None


def _write_cache(df: pd.DataFrame, cache_dir: Path, code: int) -> None:
    parquet_path, pickle_path = _cache_paths(cache_dir, code)
    try:
        df.to_parquet(parquet_path, index=False)
        return
    except Exception:
        pass

    try:
        df.to_pickle(pickle_path)
    except Exception:
        pass


def extrair_bcb(
    codigo: int,
    inicio: Any = None,
    fim: Any = None,
    cache_dir: str | Path | None = None,
    ttl_hours: int | None = None,
    timeout: int = 30,
    fallback_full_series: bool = True,
) -> pd.DataFrame:
    inicio_fmt = _normalize_date_param(inicio)
    fim_fmt = _normalize_date_param(fim)
    requested_range = bool(inicio_fmt or fim_fmt)

    if inicio_fmt and fim_fmt and pd.to_datetime(inicio_fmt, dayfirst=True) > pd.to_datetime(fim_fmt, dayfirst=True):
        raise ValueError("A data inicial nao pode ser maior que a data final.")

    cache_path = Path(cache_dir) if cache_dir else None
    if cache_path is not None:
        cache_path.mkdir(parents=True, exist_ok=True)
        cached = None if requested_range else _read_cache(cache_path, codigo, ttl_hours)
        if cached is not None:
            cached = _filter_date_range(cached, inicio_fmt, fim_fmt)
            return _apply_metadata(
                cached,
                code=int(codigo),
                requested_start=inicio_fmt,
                requested_end=fim_fmt,
                source=cached.attrs.get("source", "cache"),
                used_full_series_fallback=False,
                message="Serie carregada do cache local.",
            )

    session = _make_session()

    try:
        df = _request_series(session, int(codigo), timeout=timeout, inicio=inicio_fmt, fim=fim_fmt)
        used_full_series_fallback = False

        if fallback_full_series and (df.empty or df["valor"].notna().sum() == 0) and (inicio_fmt or fim_fmt):
            full_df = _request_series(session, int(codigo), timeout=timeout)
            full_df = _filter_date_range(full_df, inicio_fmt, fim_fmt)
            if not full_df.empty:
                df = full_df
                used_full_series_fallback = True

        if cache_path is not None and not requested_range and (not df.empty or (inicio_fmt is None and fim_fmt is None)):
            cache_df = df if not used_full_series_fallback else _request_series(session, int(codigo), timeout=timeout)
            if not cache_df.empty:
                _write_cache(cache_df, cache_path, codigo)

        message = "Serie carregada com sucesso."
        if used_full_series_fallback:
            message = "Intervalo indisponivel na API; aplicada serie completa com filtro local."

        return _apply_metadata(
            df,
            code=int(codigo),
            requested_start=inicio_fmt,
            requested_end=fim_fmt,
            source="api",
            used_full_series_fallback=used_full_series_fallback,
            message=message,
        )

    except requests.RequestException as exc:
        if cache_path is not None:
            stale = _read_cache(cache_path, codigo, ttl_hours=None)
            if stale is not None:
                stale = _filter_date_range(stale, inicio_fmt, fim_fmt)
                return _apply_metadata(
                    stale,
                    code=int(codigo),
                    requested_start=inicio_fmt,
                    requested_end=fim_fmt,
                    source="cache:stale",
                    used_full_series_fallback=False,
                    message=f"API indisponivel; usando cache antigo. Erro: {exc}",
                )
        return _empty_df(
            code=int(codigo),
            requested_start=inicio_fmt,
            requested_end=fim_fmt,
            source="error",
            message=f"Falha ao consultar o SGS: {exc}",
        )
    finally:
        session.close()


def fetch_sgs_series(code: int, timeout: int = 30) -> pd.DataFrame:
    return extrair_bcb(code, timeout=timeout)


def fetch_sgs_series_cached(
    code: int,
    cache_dir: str | Path = ".cache_sgs",
    ttl_hours: int = 12,
    timeout: int = 30,
) -> pd.DataFrame:
    return extrair_bcb(code, cache_dir=cache_dir, ttl_hours=ttl_hours, timeout=timeout)


def _read_indicators_file(path: str | Path) -> pd.DataFrame:
    source_path = Path(path)

    if source_path.suffix.lower() != ".csv":
        raise ValueError("O catalogo de indicadores deve estar no formato CSV.")

    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(source_path, sep=";", encoding=encoding)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"Nao foi possivel ler o arquivo CSV de indicadores: {last_error}")


def load_indicators_table(source_path: str | Path) -> pd.DataFrame:
    df = _read_indicators_file(source_path)
    df.columns = [str(c).strip() for c in df.columns]

    if "codigo" not in df.columns:
        raise ValueError("O arquivo CSV precisa conter a coluna 'codigo'.")
    if "key" not in df.columns:
        raise ValueError("O arquivo CSV precisa conter a coluna 'key'.")

    df["codigo"] = pd.to_numeric(df["codigo"], errors="coerce").astype("Int64")

    text_columns = ["indicador", "unidade", "nome", "periodicidade", "grupo", "tipo_grafico", "key"]
    for col in text_columns:
        if col in df.columns:
            df[col] = _clean_text_series(df[col].astype("object"))

    df["key"] = df["key"].astype(str).str.strip()

    missing_key = df["key"].eq("") | df["key"].str.lower().eq("nan")
    if missing_key.any():
        df.loc[missing_key, "key"] = df.loc[missing_key, "codigo"].astype("Int64").astype(str)

    if "acumular_12m" in df.columns:
        df["acumular_12m"] = df["acumular_12m"].map(lambda x: bool(x) if pd.notna(x) else False)

    df = df[df["key"].notna()].copy()
    df = df[~df["key"].astype(str).str.strip().isin(["", "nan"])].copy()

    return df


def _empty_series_with_meta(meta: pd.Series, message: str) -> pd.DataFrame:
    serie = pd.DataFrame(columns=["data", "valor"])
    serie.attrs["message"] = message
    serie.attrs["key"] = str(meta.get("key", ""))
    return serie


def _monthly_last_change_12m(serie: pd.DataFrame) -> pd.DataFrame:
    if serie is None or serie.empty:
        return pd.DataFrame(columns=["data", "valor"])

    monthly = serie[["data", "valor"]].copy()
    monthly["data"] = pd.to_datetime(monthly["data"], errors="coerce")
    monthly["valor"] = pd.to_numeric(monthly["valor"], errors="coerce")
    monthly = monthly.dropna(subset=["data", "valor"]).sort_values("data")
    if monthly.empty:
        return pd.DataFrame(columns=["data", "valor"])

    monthly["periodo"] = monthly["data"].dt.to_period("M")
    monthly = monthly.groupby("periodo", as_index=False).tail(1).copy()
    monthly["valor"] = monthly["valor"].pct_change(12) * 100
    monthly["data"] = monthly["periodo"].dt.to_timestamp()
    monthly = monthly.dropna(subset=["valor"])[["data", "valor"]].reset_index(drop=True)
    return monthly


def _merge_monthly_series(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    if left is None or right is None or left.empty or right.empty:
        return pd.DataFrame(columns=["data", "valor_left", "valor_right"])

    left_df = left[["data", "valor"]].copy()
    right_df = right[["data", "valor"]].copy()
    left_df["data"] = pd.to_datetime(left_df["data"], errors="coerce")
    right_df["data"] = pd.to_datetime(right_df["data"], errors="coerce")
    left_df["valor"] = pd.to_numeric(left_df["valor"], errors="coerce")
    right_df["valor"] = pd.to_numeric(right_df["valor"], errors="coerce")
    left_df = left_df.dropna(subset=["data", "valor"])
    right_df = right_df.dropna(subset=["data", "valor"])
    if left_df.empty or right_df.empty:
        return pd.DataFrame(columns=["data", "valor_left", "valor_right"])

    left_df["periodo"] = left_df["data"].dt.to_period("M")
    right_df["periodo"] = right_df["data"].dt.to_period("M")
    merged = (
        left_df.groupby("periodo", as_index=False).tail(1)[["periodo", "valor"]]
        .rename(columns={"valor": "valor_left"})
        .merge(
            right_df.groupby("periodo", as_index=False).tail(1)[["periodo", "valor"]].rename(columns={"valor": "valor_right"}),
            on="periodo",
            how="inner",
        )
        .sort_values("periodo")
        .reset_index(drop=True)
    )
    if merged.empty:
        return pd.DataFrame(columns=["data", "valor_left", "valor_right"])
    merged["data"] = merged["periodo"].dt.to_timestamp()
    return merged[["data", "valor_left", "valor_right"]]


def _build_derived_series(meta: pd.Series, by_key: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    key = str(meta.get("key", "")).strip()

    if key == "saldo_tc_idp_12m":
        tc = by_key.get("transacoes_correntes")
        idp = by_key.get("ide_pais_12m")

        if tc is None or idp is None or tc.empty or idp.empty:
            return _empty_series_with_meta(meta, "Dependencias ausentes para calcular a serie derivada.")

        merged = (
            tc[["data", "valor"]]
            .rename(columns={"valor": "valor_tc"})
            .merge(
                idp[["data", "valor"]].rename(columns={"valor": "valor_idp"}),
                on="data",
                how="inner",
            )
            .sort_values("data")
            .reset_index(drop=True)
        )
        merged["valor"] = merged["valor_tc"] - merged["valor_idp"]
        derived = merged[["data", "valor"]].copy()
        derived.attrs["message"] = "Serie derivada calculada localmente a partir do catalogo."
        return derived

    if key == "m1_var_12m":
        m1 = by_key.get("agregado_monetario_m1")
        if m1 is None or m1.empty:
            return _empty_series_with_meta(meta, "Dependencias ausentes para calcular a serie derivada.")

        derived = _monthly_last_change_12m(m1)
        if derived.empty:
            return _empty_series_with_meta(meta, "Nao foi possivel calcular a variacao acumulada em 12 meses do M1.")
        derived.attrs["message"] = "Serie derivada calculada localmente a partir do M1 diario."
        return derived

    if key == "inflacao12_m1yoy":
        m1_yoy = by_key.get("m1_var_12m")
        ipca_12m = by_key.get("ipca_12_meses")
        merged = _merge_monthly_series(m1_yoy, ipca_12m)
        if merged.empty:
            return _empty_series_with_meta(meta, "Dependencias ausentes para calcular a serie comparativa.")

        merged["valor"] = merged["valor_left"] - merged["valor_right"]
        derived = merged[["data", "valor"]].copy()
        derived.attrs["message"] = "Serie comparativa calculada localmente a partir de M1 YoY e IPCA 12 meses."
        return derived

    return _empty_series_with_meta(meta, "Serie sem codigo SGS e sem regra de derivacao configurada.")


def _buffered_start_date(start: Any, periodicidade: Any) -> Any:
    if start in (None, ""):
        return None

    start_ts = pd.to_datetime(start, errors="coerce")
    if pd.isna(start_ts):
        return None

    periodicidade_norm = str(periodicidade or "").strip().lower()
    if periodicidade_norm == "anual":
        return start_ts - pd.DateOffset(years=10)
    if periodicidade_norm in {"mensal", "trimestral"}:
        return start_ts - pd.DateOffset(years=5)
    if periodicidade_norm == "diário" or periodicidade_norm == "diario":
        return start_ts - pd.DateOffset(years=2)
    return start_ts - pd.DateOffset(years=3)


def fetch_all_indicators(
    indicators_df: pd.DataFrame,
    use_disk_cache: bool = True,
    cache_dir: str | Path = ".cache_sgs",
    ttl_hours: int = 12,
    timeout: int = 30,
    inicio: Any = None,
    fim: Any = None,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    rows = []
    by_key: Dict[str, pd.DataFrame] = {}

    coded_rows = indicators_df[indicators_df["codigo"].notna()].copy()
    derived_rows = indicators_df[indicators_df["codigo"].isna()].copy()

    coded_meta_rows = [(seq, meta) for seq, (_, meta) in enumerate(coded_rows.iterrows())]

    def _fetch_one(seq_meta: tuple[int, pd.Series]) -> tuple[int, str, int, pd.Series, pd.DataFrame]:
        seq, meta = seq_meta
        code = int(meta["codigo"])
        key = str(meta.get("key", code))
        periodicidade = meta.get("periodicidade")
        buffered_inicio = _buffered_start_date(inicio, periodicidade)

        try:
            if use_disk_cache:
                serie = extrair_bcb(
                    code,
                    cache_dir=cache_dir,
                    ttl_hours=ttl_hours,
                    timeout=timeout,
                    inicio=buffered_inicio,
                    fim=fim,
                )
            else:
                serie = extrair_bcb(
                    code,
                    timeout=timeout,
                    inicio=buffered_inicio,
                    fim=fim,
                )
        except Exception as exc:
            serie = pd.DataFrame(columns=["data", "valor"])
            serie.attrs["message"] = f"Falha ao carregar a serie {code}: {exc}"

        return seq, key, code, meta, serie

    max_workers = min(12, max(1, len(coded_meta_rows)))
    fetched_results: list[tuple[int, str, int, pd.Series, pd.DataFrame]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_fetch_one, seq_meta): seq_meta for seq_meta in coded_meta_rows}
        for future in as_completed(future_map):
            fetched_results.append(future.result())

    fetched_results.sort(key=lambda item: item[0])

    for _, key, code, meta, serie in fetched_results:
        by_key[key] = serie.copy()

        if serie.empty:
            continue

        tmp = serie.copy()
        tmp["codigo"] = code
        tmp["key"] = key

        for c in [
            "nome",
            "indicador",
            "unidade",
            "grupo",
            "periodicidade",
            "tipo_grafico",
            "acumular_12m",
            "mostrar_dashboard",
            "ordem",
        ]:
            if c in indicators_df.columns:
                tmp[c] = meta.get(c)

        rows.append(tmp)

    for _, meta in derived_rows.iterrows():
        key = str(meta.get("key", "")).strip()
        if not key:
            continue

        serie = _build_derived_series(meta, by_key)
        by_key[key] = serie.copy()

        if serie.empty:
            continue

        tmp = serie.copy()
        tmp["codigo"] = pd.NA
        tmp["key"] = key

        for c in [
            "nome",
            "indicador",
            "unidade",
            "grupo",
            "periodicidade",
            "tipo_grafico",
            "acumular_12m",
            "mostrar_dashboard",
            "ordem",
        ]:
            if c in indicators_df.columns:
                tmp[c] = meta.get(c)

        rows.append(tmp)

    if rows:
        df_long = pd.concat(rows, ignore_index=True)
        df_long = df_long.sort_values(["key", "data"]).reset_index(drop=True)
    else:
        df_long = pd.DataFrame(
            columns=[
                "data",
                "valor",
                "codigo",
                "key",
                "nome",
                "indicador",
                "unidade",
                "grupo",
                "periodicidade",
                "tipo_grafico",
                "acumular_12m",
                "mostrar_dashboard",
                "ordem",
            ]
        )

    return df_long, by_key
