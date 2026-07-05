from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests

from yahoo_csv_utils import rebuild_count_csv, sort_option_data


ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "data" / "csv"
REPORT_JSON = ROOT / "synthetic_backfill_report.json"
REPORT_CSV = ROOT / "synthetic_backfill_report.csv"
DATE_FORMAT = "%d%b%Y"

ACTIVE_TICKERS = [
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

MARKET_HOLIDAYS = {
    date(2026, 2, 16),  # Presidents Day
    date(2026, 4, 3),  # Good Friday
    date(2026, 5, 25),  # Memorial Day
    date(2026, 6, 19),  # Juneteenth
    date(2026, 7, 3),  # Observed Independence Day
}

CONTRACT_KEY = ["cp_flag", "exdateraw", "x"]
INTERPOLATED_COLUMNS = ["s", "tr", "oprice", "volume", "iv", "deltachk"]
OUTPUT_COLUMNS = [
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


@dataclass
class TickerReport:
    ticker: str
    inserted_dates: list[str]
    inserted_rows: int
    old_rows: int
    new_rows: int
    old_dates: int
    new_dates: int
    upload_status: str


def parse_yyyymmdd(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_dateraw(value: date | pd.Timestamp) -> str:
    return pd.Timestamp(value).strftime(DATE_FORMAT)


def trading_days(start: date, end_exclusive: date) -> list[date]:
    return [
        current.date()
        for current in pd.date_range(start, end_exclusive - pd.Timedelta(days=1), freq="D")
        if current.weekday() < 5 and current.date() not in MARKET_HOLIDAYS
    ]


def parse_dateraw_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, format=DATE_FORMAT, errors="raise")


def date_hashes(df: pd.DataFrame) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for dateraw, group in sort_option_data(df).groupby("dateraw", sort=False):
        payload = group.to_csv(index=False, lineterminator="\n")
        hashes[str(dateraw)] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return hashes


def money_from_row(row: pd.Series) -> float:
    return float(np.log((float(row["x"]) / 1000.0) * np.exp(-float(row["tr"]) * float(row["tauday"]) / 252.0) / float(row["s"])))


def recompute_derived_columns(df: pd.DataFrame, synthetic_date: date) -> pd.DataFrame:
    out = df.copy()
    exp_dates = parse_dateraw_series(out["exdateraw"])
    out["tauday"] = (exp_dates.dt.date - synthetic_date).map(lambda delta: delta.days)
    out = out[out["tauday"] > 8].copy()
    if out.empty:
        return out

    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(0).clip(lower=0)
    out["iv"] = pd.to_numeric(out["iv"], errors="coerce").fillna(0.000001).clip(lower=0.000001)
    out["oprice"] = pd.to_numeric(out["oprice"], errors="coerce").fillna(0).clip(lower=0)
    out["money"] = out.apply(money_from_row, axis=1)
    out["dateraw"] = format_dateraw(synthetic_date)
    return out[OUTPUT_COLUMNS]


def rows_by_contract(group: pd.DataFrame) -> dict[tuple[str, str, float], pd.Series]:
    deduped = group.drop_duplicates(subset=CONTRACT_KEY, keep="last")
    return {
        (str(row["cp_flag"]), str(row["exdateraw"]), float(row["x"])): row
        for _, row in deduped.iterrows()
    }


def contract_key_series(df: pd.DataFrame) -> pd.Series:
    return (
        df["cp_flag"].astype(str)
        + "\0"
        + df["exdateraw"].astype(str)
        + "\0"
        + pd.to_numeric(df["x"], errors="coerce").astype(str)
    )


def contract_key_tuple(row: pd.Series) -> tuple[str, str, float]:
    return (str(row["cp_flag"]), str(row["exdateraw"]), float(row["x"]))


def interpolate_rows(
    synthetic_date: date,
    left_date: date,
    left_group: pd.DataFrame,
    right_date: date,
    right_group: pd.DataFrame,
) -> pd.DataFrame:
    left_rows = rows_by_contract(left_group)
    right_rows = rows_by_contract(right_group)
    total_days = (right_date - left_date).days
    ratio = (synthetic_date - left_date).days / total_days
    output: list[dict[str, object]] = []

    for key in sorted(set(left_rows) | set(right_rows)):
        left = left_rows.get(key)
        right = right_rows.get(key)
        if left is not None and right is not None:
            row = left.copy()
            for column in INTERPOLATED_COLUMNS:
                row[column] = float(left[column]) + (float(right[column]) - float(left[column])) * ratio
        else:
            left_distance = abs((synthetic_date - left_date).days)
            right_distance = abs((right_date - synthetic_date).days)
            if left is None:
                row = right.copy()
            elif right is None:
                row = left.copy()
            else:
                row = (left if left_distance <= right_distance else right).copy()
        output.append(row.to_dict())

    return recompute_derived_columns(pd.DataFrame(output), synthetic_date)


def extrapolate_rows(
    synthetic_date: date,
    latest_date: date,
    latest_group: pd.DataFrame,
    history: pd.DataFrame,
) -> pd.DataFrame:
    latest_contracts = latest_group.drop_duplicates(subset=CONTRACT_KEY, keep="last").copy()
    latest_keys = set(contract_key_series(latest_contracts).tolist())
    history_with_dates = history.copy()
    history_with_dates["_date"] = parse_dateraw_series(history_with_dates["dateraw"]).dt.date
    history_with_dates["_key"] = contract_key_series(history_with_dates)
    prior_rows = (
        history_with_dates.loc[(history_with_dates["_date"] < latest_date) & history_with_dates["_key"].isin(latest_keys)]
        .sort_values("_date")
        .drop_duplicates(subset=CONTRACT_KEY, keep="last")
    )
    previous_by_key = rows_by_contract(prior_rows.drop(columns=["_date", "_key"]))
    previous_dates = dict(zip((contract_key_tuple(row) for _, row in prior_rows.iterrows()), prior_rows["_date"]))

    output: list[dict[str, object]] = []
    for _, latest in latest_contracts.iterrows():
        key = contract_key_tuple(latest)
        row = latest.copy()
        previous = previous_by_key.get(key)
        previous_date = previous_dates.get(key)
        if previous is not None and previous_date is not None:
            elapsed = max((latest_date - previous_date).days, 1)
            ahead = (synthetic_date - latest_date).days
            for column in INTERPOLATED_COLUMNS:
                slope = (float(latest[column]) - float(previous[column])) / elapsed
                row[column] = float(latest[column]) + slope * ahead
        output.append(row.to_dict())

    return recompute_derived_columns(pd.DataFrame(output), synthetic_date)


def find_neighbor_dates(real_dates: list[date], target: date) -> tuple[date | None, date | None]:
    before = [item for item in real_dates if item < target]
    after = [item for item in real_dates if item > target]
    return (before[-1] if before else None, after[0] if after else None)


def read_blob_csv(base_url: str, blob_path: str) -> pd.DataFrame | None:
    response = requests.get(f"{base_url.rstrip('/')}/{blob_path}", timeout=60)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))


def load_source_csv(ticker: str, source: str) -> pd.DataFrame:
    data_path = CSV_DIR / f"optout_{ticker}.csv"
    if source in {"auto", "local"} and data_path.exists():
        return pd.read_csv(data_path)

    if source in {"auto", "blob"}:
        base_url = os.getenv("BLOB_BASE_URL")
        if not base_url:
            if source == "blob":
                raise EnvironmentError("BLOB_BASE_URL environment variable is not set.")
        else:
            blob_df = read_blob_csv(base_url, f"csv/optout_{ticker}.csv")
            if blob_df is not None:
                return blob_df

    raise FileNotFoundError(data_path)


def upload_to_blob(path: Path, blob_path: str) -> str:
    token = os.getenv("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise EnvironmentError("BLOB_READ_WRITE_TOKEN environment variable is not set.")
    with path.open("rb") as handle:
        response = requests.put(
            f"https://blob.vercel-storage.com/{blob_path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/csv",
                "x-add-random-suffix": "0",
                "x-cache-control-max-age": "0",
            },
            data=handle,
            timeout=120,
        )
    if response.status_code not in {200, 201}:
        raise RuntimeError(f"Blob upload failed for {blob_path}: HTTP {response.status_code} - {response.text}")
    return "uploaded"


def backfill_ticker(
    ticker: str,
    target_days: list[date],
    dry_run: bool,
    upload_blob: bool,
    source: str,
) -> TickerReport:
    data_path = CSV_DIR / f"optout_{ticker}.csv"
    count_path = CSV_DIR / f"optout_{ticker}_count.csv"

    df = sort_option_data(load_source_csv(ticker, source))
    old_rows = len(df)
    existing_hashes = date_hashes(df)
    parsed_dates = parse_dateraw_series(df["dateraw"])
    real_dates = sorted(parsed_dates.dt.date.unique().tolist())
    existing_dates = set(real_dates)
    missing_dates = [item for item in target_days if item not in existing_dates]

    generated_frames: list[pd.DataFrame] = []
    for missing_date in missing_dates:
        left_date, right_date = find_neighbor_dates(real_dates, missing_date)
        if left_date is None:
            raise ValueError(f"{ticker}: no real observation before {missing_date}")

        left_group = df.loc[parsed_dates.dt.date == left_date]
        if right_date is not None:
            right_group = df.loc[parsed_dates.dt.date == right_date]
            generated = interpolate_rows(missing_date, left_date, left_group, right_date, right_group)
        else:
            generated = extrapolate_rows(missing_date, left_date, left_group, df)
        if generated.empty:
            raise ValueError(f"{ticker}: generated no usable rows for {missing_date}")
        generated_frames.append(generated)

    if generated_frames:
        new_df = sort_option_data(pd.concat([df, *generated_frames], ignore_index=True))
    else:
        new_df = df

    new_hashes = date_hashes(new_df[new_df["dateraw"].isin(existing_hashes)])
    changed_real_dates = [dateraw for dateraw, digest in existing_hashes.items() if new_hashes.get(dateraw) != digest]
    if changed_real_dates:
        raise ValueError(f"{ticker}: existing real rows changed for {changed_real_dates[:5]}")

    expected_dates = {format_dateraw(item) for item in target_days}
    actual_dates = set(new_df["dateraw"].astype(str).unique().tolist())
    if actual_dates != expected_dates:
        missing = sorted(expected_dates - actual_dates)
        extra = sorted(actual_dates - expected_dates)
        raise ValueError(f"{ticker}: date validation failed; missing={missing[:5]}, extra={extra[:5]}")
    if "03Jul2026" in actual_dates:
        raise ValueError(f"{ticker}: found forbidden observed-holiday date 03Jul2026")

    if not dry_run:
        new_df.to_csv(data_path, index=False)
        counts = rebuild_count_csv(data_path, count_path)
        if int(counts["count"].sum()) != len(new_df):
            raise ValueError(f"{ticker}: count CSV total does not equal detail row count")

    upload_status = "not_requested"
    if upload_blob:
        if dry_run:
            upload_status = "dry_run_skipped"
        else:
            upload_status = upload_to_blob(data_path, f"csv/optout_{ticker}.csv")

    return TickerReport(
        ticker=ticker,
        inserted_dates=[item.isoformat() for item in missing_dates],
        inserted_rows=sum(len(frame) for frame in generated_frames),
        old_rows=old_rows,
        new_rows=len(new_df),
        old_dates=len(existing_dates),
        new_dates=len(parse_dateraw_series(new_df["dateraw"]).dt.date.unique()),
        upload_status=upload_status,
    )


def validate_outputs(tickers: Iterable[str], target_days: list[date], dry_run: bool) -> None:
    if dry_run:
        return

    expected = {format_dateraw(item) for item in target_days}
    forbidden = "03Jul2026"
    for ticker in tickers:
        data_path = CSV_DIR / f"optout_{ticker}.csv"
        count_path = CSV_DIR / f"optout_{ticker}_count.csv"
        df = pd.read_csv(data_path)
        date_values = set(df["dateraw"].astype(str).unique().tolist())
        if date_values != expected:
            missing = sorted(expected - date_values)
            extra = sorted(date_values - expected)
            raise ValueError(f"{ticker}: date validation failed; missing={missing[:5]}, extra={extra[:5]}")
        if forbidden in date_values:
            raise ValueError(f"{ticker}: found forbidden observed-holiday date {forbidden}")
        counts = pd.read_csv(count_path)
        if int(counts["count"].sum()) != len(df):
            raise ValueError(f"{ticker}: count sum does not equal detail rows")


def write_report(reports: list[TickerReport]) -> None:
    rows = [asdict(report) for report in reports]
    REPORT_JSON.write_text(json.dumps(rows, indent=2) + "\n")
    with REPORT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill synthetic option CSV rows for missing 2026 trading days.")
    parser.add_argument("--start", default="2026-01-26", help="Inclusive start date in YYYY-MM-DD format.")
    parser.add_argument("--end", default="2026-07-03", help="Exclusive end date in YYYY-MM-DD format.")
    parser.add_argument("--tickers", nargs="*", default=ACTIVE_TICKERS, help="Ticker subset to process.")
    parser.add_argument(
        "--source",
        choices=["auto", "local", "blob"],
        default="auto",
        help="Read existing CSVs from local data/csv, Blob, or local-then-Blob fallback.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Generate and validate in memory without writing CSVs.")
    parser.add_argument("--upload-blob", action="store_true", help="Upload updated detail CSVs to Vercel Blob.")
    args = parser.parse_args()

    start = parse_yyyymmdd(args.start)
    end = parse_yyyymmdd(args.end)
    target_days = trading_days(start, end)
    if start == date(2026, 1, 26) and end == date(2026, 7, 3) and len(target_days) != 110:
        raise ValueError(f"Expected 110 trading days for default backfill window, found {len(target_days)}")

    reports = [
        backfill_ticker(ticker, target_days, dry_run=args.dry_run, upload_blob=args.upload_blob, source=args.source)
        for ticker in args.tickers
    ]
    validate_outputs(args.tickers, target_days, dry_run=args.dry_run)
    write_report(reports)

    for report in reports:
        print(
            f"{report.ticker}: inserted {report.inserted_rows} rows across "
            f"{len(report.inserted_dates)} dates; {report.old_rows} -> {report.new_rows}; "
            f"upload={report.upload_status}"
        )
    print(f"Wrote {REPORT_JSON.relative_to(ROOT)} and {REPORT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
