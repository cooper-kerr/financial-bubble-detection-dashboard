import subprocess
from io import StringIO
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "data" / "csv"

BLOB_BASE_URL = "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com"
GIT_REF = "7202016"

YAHOO_TICKERS = [
    "SPX",
    "AAPL",
    "BAC",
    "C",
    "MSFT",
    "GE",
    "INTC",
    "CSCO",
    "BABA",
    "WFC",
    "JPM",
    "AMD",
    "META",
    "F",
    "TSLA",
    "GOOG",
    "T",
    "XOM",
    "AMZN",
    "MS",
    "NVDA",
    "AIG",
    "GM",
    "DIS",
    "BA",
]


def read_local_csv(filename: str) -> pd.DataFrame | None:
    path = CSV_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


def read_blob_csv(filename: str) -> pd.DataFrame | None:
    response = requests.get(f"{BLOB_BASE_URL}/csv/{filename}", timeout=60)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))


def read_git_csv(filename: str) -> pd.DataFrame | None:
    result = subprocess.run(
        ["git", "show", f"{GIT_REF}:data/csv/{filename}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return pd.read_csv(StringIO(result.stdout))


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized["_date_sort"] = pd.to_datetime(
        normalized["dateraw"],
        format="%d%b%Y",
        errors="raise",
    )
    return normalized


def merge_by_date(
    local_df: pd.DataFrame | None,
    blob_df: pd.DataFrame | None,
    git_df: pd.DataFrame | None,
) -> pd.DataFrame:
    rows_by_date: dict[str, pd.DataFrame] = {}

    # Later sources win for a whole date, which keeps detail and count files
    # aligned with the source that produced that date's option-chain snapshot.
    for df in [local_df, blob_df, git_df]:
        if df is None or df.empty:
            continue
        for dateraw, group in df.groupby("dateraw", sort=False):
            rows_by_date[str(dateraw)] = group.copy()

    if not rows_by_date:
        raise ValueError("No rows found in any source")

    merged = pd.concat(rows_by_date.values(), ignore_index=True)
    merged = normalize_dates(merged)
    merged = merged.sort_values("_date_sort", kind="stable").drop(columns=["_date_sort"])
    return merged


def summarize(filename: str, df: pd.DataFrame) -> str:
    dates = pd.to_datetime(df["dateraw"].unique(), format="%d%b%Y", errors="raise")
    return (
        f"{filename}: {len(df)} rows, {len(dates)} dates, "
        f"{dates.min().date()} to {dates.max().date()}"
    )


def main() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    for ticker in YAHOO_TICKERS:
        for suffix in ["", "_count"]:
            filename = f"optout_{ticker}{suffix}.csv"
            local_df = read_local_csv(filename)
            blob_df = read_blob_csv(filename)
            git_df = read_git_csv(filename)

            merged = merge_by_date(local_df, blob_df, git_df)
            merged.to_csv(CSV_DIR / filename, index=False)
            print(summarize(filename, merged))


if __name__ == "__main__":
    main()
