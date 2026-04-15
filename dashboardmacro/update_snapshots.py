# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from dados_fred import fetch_all_fred_indicators
from extrair_bcb import fetch_all_indicators, load_indicators_table


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CODES_PATH = DATA_DIR / "codes.csv"
CACHE_DIR = BASE_DIR / ".cache_sgs"
BR_SNAPSHOT_PATH = DATA_DIR / "macro_brasil_snapshot.pkl"
US_SNAPSHOT_PATH = DATA_DIR / "macro_eua_snapshot.pkl"
META_PATH = DATA_DIR / "snapshot_metadata.json"
FRED_API_KEY = "da9de0f64ae8f49db8bfc2b01d51c163"


def iso_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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


def update_macro_brasil() -> dict:
    catalog = load_indicators_table(CODES_PATH)
    df_long, _ = fetch_all_indicators(
        catalog,
        use_disk_cache=True,
        cache_dir=CACHE_DIR,
        ttl_hours=12,
        timeout=30,
    )
    df_long = normalize_frame(df_long)
    BR_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_long.to_pickle(BR_SNAPSHOT_PATH)
    return {
        "updated_at": iso_now(),
        "rows": int(len(df_long)),
        "indicators": int(df_long["key"].nunique()) if "key" in df_long.columns and not df_long.empty else 0,
        "path": str(BR_SNAPSHOT_PATH),
    }


def update_macro_eua() -> dict:
    df_long, _, catalog = fetch_all_fred_indicators(FRED_API_KEY)
    df_long = normalize_frame(df_long)
    US_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_long.to_pickle(US_SNAPSHOT_PATH)
    return {
        "updated_at": iso_now(),
        "rows": int(len(df_long)),
        "indicators": int(len(catalog)),
        "path": str(US_SNAPSHOT_PATH),
    }


def main() -> None:
    print("Atualizando snapshot Macro Brasil...")
    br_meta = update_macro_brasil()
    print(f"Macro Brasil OK: {br_meta['rows']} linhas, {br_meta['indicators']} indicadores.")

    print("Atualizando snapshot Macro EUA...")
    us_meta = update_macro_eua()
    print(f"Macro EUA OK: {us_meta['rows']} linhas, {us_meta['indicators']} indicadores.")

    write_metadata(
        {
            "generated_at": iso_now(),
            "macro_brasil": br_meta,
            "macro_eua": us_meta,
        }
    )
    print(f"Metadados salvos em {META_PATH}")


if __name__ == "__main__":
    main()
