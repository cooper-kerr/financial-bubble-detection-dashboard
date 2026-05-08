import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
LOCAL_CSV_DIR = ROOT / "data" / "csv"
REPORT_JSON_PATH = ROOT / "blob_csv_reconciliation.json"
REPORT_CSV_PATH = ROOT / "blob_csv_reconciliation.csv"

load_dotenv(ROOT / ".env.local")

DETAIL_COLUMNS = [
    "dateraw",
    "cp_flag",
    "exdateraw",
    "tauday",
    "x",
    "s",
    "tr",
    "money",
    "oprice",
    "volume",
    "iv",
    "deltachk",
]

COUNT_COLUMNS = ["dateraw", "count"]

TICKERS = [
    "SPX",
    "AAPL",
    "BAC",
    "C",
    "MSFT",
    "FB",
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


@dataclass
class DatasetSummary:
    row_count: int
    unique_dates: int
    min_date: str | None
    max_date: str | None


@dataclass
class ComparisonResult:
    ticker: str
    dataset: str
    local_rows: int
    blob_rows: int
    local_unique_dates: int
    blob_unique_dates: int
    local_min_date: str | None
    local_max_date: str | None
    blob_min_date: str | None
    blob_max_date: str | None
    local_only_dates: int
    blob_only_dates: int
    common_dates: int
    local_only_rows: int
    blob_only_rows: int
    common_rows: int
    classification: str
    notes: str


def file_digest(rows: Iterable[str]) -> set[str]:
    return {hashlib.sha256(row.encode("utf-8")).hexdigest() for row in rows}


def normalize_dataframe(df: pd.DataFrame, expected_columns: list[str]) -> pd.DataFrame:
    missing = [column for column in expected_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    normalized = df[expected_columns].copy()
    normalized = normalized.fillna("")
    for column in expected_columns:
        normalized[column] = normalized[column].astype(str).str.strip()
    return normalized


def summarize_dates(df: pd.DataFrame) -> DatasetSummary:
    if df.empty:
        return DatasetSummary(row_count=0, unique_dates=0, min_date=None, max_date=None)

    dates = pd.to_datetime(
        df["dateraw"].astype(str).unique().tolist(),
        format="%d%b%Y",
        errors="raise",
    ).sort_values()
    return DatasetSummary(
        row_count=len(df),
        unique_dates=len(dates),
        min_date=dates[0].strftime("%d%b%Y"),
        max_date=dates[-1].strftime("%d%b%Y"),
    )


def classify_relationship(
    local_only_rows: int,
    blob_only_rows: int,
    local_only_dates: int,
    blob_only_dates: int,
) -> tuple[str, str]:
    if local_only_rows == 0 and blob_only_rows == 0:
        return "identical", "All compared rows match exactly."
    if blob_only_rows == 0:
        if local_only_dates > 0:
            return "blob_subset_of_local", "Blob data is a strict subset of the local backup."
        return "blob_rows_subset_of_local", "Blob rows are a strict subset of the local backup on overlapping dates."
    if local_only_rows == 0:
        if blob_only_dates > 0:
            return "local_subset_of_blob", "Local backup is a strict subset of Blob data."
        return "local_rows_subset_of_blob", "Local rows are a strict subset of Blob data on overlapping dates."
    if local_only_dates > 0 and blob_only_dates > 0:
        return "divergent_date_ranges", "Both datasets contain exclusive dates."
    return "divergent_overlap", "Datasets overlap in date coverage but differ in row content."


def compare_frames(ticker: str, dataset: str, local_df: pd.DataFrame, blob_df: pd.DataFrame) -> ComparisonResult:
    local_summary = summarize_dates(local_df)
    blob_summary = summarize_dates(blob_df)

    local_dates = set(local_df["dateraw"].astype(str).unique().tolist())
    blob_dates = set(blob_df["dateraw"].astype(str).unique().tolist())

    local_rows = file_digest(local_df.to_csv(index=False, header=False, lineterminator="\n").splitlines())
    blob_rows = file_digest(blob_df.to_csv(index=False, header=False, lineterminator="\n").splitlines())

    local_only_rows = len(local_rows - blob_rows)
    blob_only_rows = len(blob_rows - local_rows)
    common_rows = len(local_rows & blob_rows)
    local_only_dates = len(local_dates - blob_dates)
    blob_only_dates = len(blob_dates - local_dates)
    common_dates = len(local_dates & blob_dates)
    classification, notes = classify_relationship(
        local_only_rows=local_only_rows,
        blob_only_rows=blob_only_rows,
        local_only_dates=local_only_dates,
        blob_only_dates=blob_only_dates,
    )

    return ComparisonResult(
        ticker=ticker,
        dataset=dataset,
        local_rows=local_summary.row_count,
        blob_rows=blob_summary.row_count,
        local_unique_dates=local_summary.unique_dates,
        blob_unique_dates=blob_summary.unique_dates,
        local_min_date=local_summary.min_date,
        local_max_date=local_summary.max_date,
        blob_min_date=blob_summary.min_date,
        blob_max_date=blob_summary.max_date,
        local_only_dates=local_only_dates,
        blob_only_dates=blob_only_dates,
        common_dates=common_dates,
        local_only_rows=local_only_rows,
        blob_only_rows=blob_only_rows,
        common_rows=common_rows,
        classification=classification,
        notes=notes,
    )


def fetch_blob_csv(base_url: str, blob_path: str) -> pd.DataFrame:
    response = requests.get(f"{base_url}/{blob_path}", timeout=60)
    if response.status_code == 404:
        raise FileNotFoundError(blob_path)
    response.raise_for_status()
    return pd.read_csv(pd.io.common.StringIO(response.text))


def reconcile_ticker(base_url: str, ticker: str) -> list[ComparisonResult]:
    results: list[ComparisonResult] = []
    for suffix, columns, dataset_name in [
        ("", DETAIL_COLUMNS, "detail"),
        ("_count", COUNT_COLUMNS, "count"),
    ]:
        filename = f"optout_{ticker}{suffix}.csv"
        local_path = LOCAL_CSV_DIR / filename
        if not local_path.exists():
            raise FileNotFoundError(f"Local CSV missing: {local_path}")

        local_df = normalize_dataframe(pd.read_csv(local_path), columns)
        blob_df = normalize_dataframe(fetch_blob_csv(base_url, f"csv/{filename}"), columns)
        results.append(compare_frames(ticker, dataset_name, local_df, blob_df))
    return results


def write_reports(results: list[ComparisonResult]) -> None:
    REPORT_JSON_PATH.write_text(
        json.dumps([asdict(result) for result in results], indent=2),
        encoding="utf-8",
    )

    with REPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def main() -> None:
    base_url = os.getenv("BLOB_BASE_URL")
    if not base_url:
        raise EnvironmentError("BLOB_BASE_URL environment variable is required.")

    results: list[ComparisonResult] = []
    failures: list[dict[str, str]] = []

    for ticker in TICKERS:
        try:
            results.extend(reconcile_ticker(base_url, ticker))
        except Exception as error:
            failures.append({"ticker": ticker, "error": str(error)})

    if results:
        write_reports(results)

    summary_counts: dict[str, int] = {}
    for result in results:
        summary_counts[result.classification] = summary_counts.get(result.classification, 0) + 1

    print("CSV reconciliation summary")
    for classification, count in sorted(summary_counts.items()):
        print(f"- {classification}: {count}")

    print(f"\nDetailed JSON report: {REPORT_JSON_PATH}")
    print(f"Detailed CSV report: {REPORT_CSV_PATH}")

    if failures:
        print("\nFailures")
        for failure in failures:
            print(f"- {failure['ticker']}: {failure['error']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
