# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from dados_fred import fetch_all_fred_indicators
from extrair_bcb import fetch_all_indicators, load_indicators_table
from src.dados_tesouro import dados_tesouro


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CODES_PATH = DATA_DIR / "codes.csv"
CACHE_DIR = BASE_DIR / ".cache_sgs"
BR_SNAPSHOT_PATH = DATA_DIR / "macro_brasil_snapshot.pkl"
BR_SNAPSHOT_CSV_PATH = DATA_DIR / "macro_brasil_snapshot.csv.gz"
US_SNAPSHOT_PATH = DATA_DIR / "macro_eua_snapshot.pkl"
US_SNAPSHOT_CSV_PATH = DATA_DIR / "macro_eua_snapshot.csv.gz"
TESOURO_SNAPSHOT_PATH = DATA_DIR / "tesouro_direto_snapshot.pkl"
TESOURO_SNAPSHOT_CSV_PATH = DATA_DIR / "tesouro_direto_snapshot.csv.gz"
META_PATH = DATA_DIR / "snapshot_metadata.json"
FRED_API_KEY = "da9de0f64ae8f49db8bfc2b01d51c163"
TESOURO_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/"
    "precotaxatesourodireto.csv"
)


def iso_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except Exception:
        return str(path)


def write_metadata(meta: dict) -> None:
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "data" in out.columns:
        out["data"] = pd.to_datetime(out["data"], errors="coerce")
    if "valor" in out.columns:
        out["valor"] = pd.to_numeric(out["valor"], errors="coerce")
    if "key" in out.columns:
        out["key"] = out["key"].astype(str)
    out = out.dropna(subset=[col for col in ["data"] if col in out.columns])
    sort_cols = [col for col in ["key", "data"] if col in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols).reset_index(drop=True)
    return out


def write_snapshot(df: pd.DataFrame, pickle_path: Path, csv_path: Path) -> None:
    pickle_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(pickle_path)
    df.to_csv(csv_path, index=False, compression="gzip")


def update_macro_brasil() -> dict:
    catalog = load_indicators_table(CODES_PATH)
    df_long, _ = fetch_all_indicators(
        catalog,
        use_disk_cache=False,
        cache_dir=CACHE_DIR,
        ttl_hours=0,
        timeout=30,
    )
    df_long = normalize_frame(df_long)
    write_snapshot(df_long, BR_SNAPSHOT_PATH, BR_SNAPSHOT_CSV_PATH)
    return {
        "updated_at": iso_now(),
        "rows": int(len(df_long)),
        "indicators": int(df_long["key"].nunique()) if "key" in df_long.columns and not df_long.empty else 0,
        "path": rel_path(BR_SNAPSHOT_CSV_PATH),
    }


def update_macro_eua() -> dict:
    df_long, _, catalog = fetch_all_fred_indicators(FRED_API_KEY)
    df_long = normalize_frame(df_long)
    write_snapshot(df_long, US_SNAPSHOT_PATH, US_SNAPSHOT_CSV_PATH)
    return {
        "updated_at": iso_now(),
        "rows": int(len(df_long)),
        "indicators": int(len(catalog)),
        "path": rel_path(US_SNAPSHOT_CSV_PATH),
    }


def update_tesouro_direto() -> dict:
    df = dados_tesouro(TESOURO_URL)
    df = df.sort_values(["Tipo Titulo", "Data Vencimento", "Data Base"]).reset_index(drop=True)
    write_snapshot(df, TESOURO_SNAPSHOT_PATH, TESOURO_SNAPSHOT_CSV_PATH)
    return {
        "updated_at": iso_now(),
        "rows": int(len(df)),
        "titles": int(df["Tipo Titulo"].nunique()) if "Tipo Titulo" in df.columns and not df.empty else 0,
        "path": rel_path(TESOURO_SNAPSHOT_CSV_PATH),
    }


def main() -> None:
    print("Atualizando snapshot Macro Brasil...")
    br_meta = update_macro_brasil()
    print(f"Macro Brasil OK: {br_meta['rows']} linhas, {br_meta['indicators']} indicadores.")

    print("Atualizando snapshot Macro EUA...")
    us_meta = update_macro_eua()
    print(f"Macro EUA OK: {us_meta['rows']} linhas, {us_meta['indicators']} indicadores.")

    print("Atualizando snapshot Renda Fixa...")
    tesouro_meta = update_tesouro_direto()
    print(f"Renda Fixa OK: {tesouro_meta['rows']} linhas, {tesouro_meta['titles']} tipos de título.")

    write_metadata(
        {
            "generated_at": iso_now(),
            "macro_brasil": br_meta,
            "macro_eua": us_meta,
            "tesouro_direto": tesouro_meta,
        }
    )
    print(f"Metadados salvos em {META_PATH}")


if __name__ == "__main__":
    main()
