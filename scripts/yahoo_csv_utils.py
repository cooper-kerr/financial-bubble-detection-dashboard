from __future__ import annotations

from pathlib import Path

import pandas as pd


DATE_COLUMN = "dateraw"
COUNT_COLUMN = "count"
DATE_FORMAT = "%d%b%Y"
DATA_SORT_COLUMNS = ["dateraw", "cp_flag", "tauday", "x", "exdateraw"]
DATA_IDENTITY_COLUMNS = ["dateraw", "cp_flag", "tauday", "x"]


def _date_sort_key(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format=DATE_FORMAT, errors="coerce")


def sort_option_data(df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in DATA_SORT_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Option CSV missing required columns for sorting: {missing}")

    sorted_df = df.copy()
    sorted_df["_parsed_dateraw"] = _date_sort_key(sorted_df[DATE_COLUMN])
    sorted_df["_parsed_exdateraw"] = _date_sort_key(sorted_df["exdateraw"])
    if sorted_df["_parsed_dateraw"].isna().any():
        bad_dates = sorted_df.loc[sorted_df["_parsed_dateraw"].isna(), DATE_COLUMN].unique()
        raise ValueError(f"Option CSV has unparsable dateraw values: {bad_dates[:5]}")

    sorted_df = sorted_df.sort_values(
        by=["_parsed_dateraw", "cp_flag", "tauday", "x", "_parsed_exdateraw"],
        kind="mergesort",
    ).drop(columns=["_parsed_dateraw", "_parsed_exdateraw"])
    return sorted_df.reset_index(drop=True)


def merge_sort_option_data(existing_df: pd.DataFrame | None, new_df: pd.DataFrame) -> pd.DataFrame:
    frames = [frame for frame in (existing_df, new_df) if frame is not None and not frame.empty]
    if not frames:
        return new_df.copy()

    merged = pd.concat(frames, ignore_index=True)
    missing_identity = [column for column in DATA_IDENTITY_COLUMNS if column not in merged.columns]
    if missing_identity:
        raise ValueError(f"Option CSV missing required identity columns: {missing_identity}")

    merged = merged.drop_duplicates(subset=DATA_IDENTITY_COLUMNS, keep="last")
    return sort_option_data(merged)


def rebuild_count_frame(data_df: pd.DataFrame) -> pd.DataFrame:
    sorted_df = sort_option_data(data_df)
    counts = (
        sorted_df.groupby(DATE_COLUMN, sort=False)
        .size()
        .reset_index(name=COUNT_COLUMN)
    )
    if int(counts[COUNT_COLUMN].sum()) != len(sorted_df):
        raise ValueError("Count rebuild failed: grouped count total does not match data rows")
    return counts


def rebuild_count_csv(data_csv: str | Path, count_csv: str | Path) -> pd.DataFrame:
    data_path = Path(data_csv)
    count_path = Path(count_csv)
    if not data_path.exists():
        raise FileNotFoundError(f"Data CSV not found: {data_path}")

    data_df = pd.read_csv(data_path)
    sorted_df = sort_option_data(data_df)
    sorted_df.to_csv(data_path, index=False)

    counts = rebuild_count_frame(sorted_df)
    count_path.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(count_path, index=False)
    return counts
