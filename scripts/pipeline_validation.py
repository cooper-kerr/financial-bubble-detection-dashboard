from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


OPTION_COLUMNS = {
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
}
PRICE_COLUMNS = {"date", "regular", "adjusted"}


def _read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise ValueError(f"missing required {label}: {path}")
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise ValueError(f"malformed {label} {path}: {exc}") from exc
    if frame.empty:
        raise ValueError(f"empty required {label}: {path}")
    return frame


def validate_ticker_staging(
    ticker: str,
    csv_dir: str | Path = "data/csv",
    price_dir: str | Path = "data/prices",
) -> dict[str, int | str]:
    csv_path = Path(csv_dir) / f"optout_{ticker}.csv"
    count_path = Path(csv_dir) / f"optout_{ticker}_count.csv"
    price_path = Path(price_dir) / f"{ticker}.csv"
    options = _read_required_csv(csv_path, f"option CSV for {ticker}")
    counts = _read_required_csv(count_path, f"count CSV for {ticker}")
    prices = _read_required_csv(price_path, f"canonical price CSV for {ticker}")

    missing_options = sorted(OPTION_COLUMNS - set(options.columns))
    if missing_options:
        raise ValueError(f"{ticker} option CSV missing columns: {missing_options}")
    if not {"dateraw", "count"}.issubset(counts.columns):
        raise ValueError(f"{ticker} count CSV must contain dateraw,count")
    missing_prices = sorted(PRICE_COLUMNS - set(prices.columns))
    if missing_prices:
        raise ValueError(f"{ticker} price CSV missing columns: {missing_prices}")

    option_dates = pd.to_datetime(options["dateraw"], format="%d%b%Y", errors="coerce")
    expiration_dates = pd.to_datetime(options["exdateraw"], format="%d%b%Y", errors="coerce")
    price_dates = pd.to_datetime(prices["date"], format="%Y-%m-%d", errors="coerce")
    if option_dates.isna().any():
        raise ValueError(f"{ticker} option CSV contains unparsable dateraw values")
    if expiration_dates.isna().any():
        raise ValueError(f"{ticker} option CSV contains unparsable exdateraw values")
    if price_dates.isna().any():
        raise ValueError(f"{ticker} price CSV contains unparsable dates")

    flags = set(options["cp_flag"].dropna().astype(str).str.upper())
    if not {"C", "P"}.issubset(flags):
        raise ValueError(f"{ticker} option CSV lacks call/put coverage: found {sorted(flags)}")

    per_date_flags = options.assign(_date=option_dates).groupby("_date")["cp_flag"].agg(
        lambda values: set(values.astype(str).str.upper())
    )
    incomplete = [date.strftime("%Y-%m-%d") for date, values in per_date_flags.items() if not {"C", "P"}.issubset(values)]
    if incomplete:
        raise ValueError(f"{ticker} option dates lack call/put coverage: {incomplete[:5]}")

    for column in ("x", "s", "oprice"):
        numeric = pd.to_numeric(options[column], errors="coerce")
        if not np.isfinite(numeric.to_numpy(dtype=float)).all():
            raise ValueError(f"{ticker} option CSV contains non-finite {column} values")
    for column in ("regular", "adjusted"):
        numeric = pd.to_numeric(prices[column], errors="coerce")
        if not np.isfinite(numeric.to_numpy(dtype=float)).all():
            raise ValueError(f"{ticker} price CSV contains non-finite {column} values")

    normalized_option_dates = set(option_dates.dt.strftime("%Y-%m-%d"))
    normalized_price_dates = set(price_dates.dt.strftime("%Y-%m-%d"))
    missing_dates = sorted(normalized_option_dates - normalized_price_dates)
    if missing_dates:
        raise ValueError(
            f"{ticker} canonical prices do not cover option dates: {missing_dates[:5]}"
        )

    count_dates = pd.to_datetime(counts["dateraw"], format="%d%b%Y", errors="coerce")
    count_values = pd.to_numeric(counts["count"], errors="coerce")
    if count_dates.isna().any() or count_values.isna().any():
        raise ValueError(f"{ticker} count CSV contains malformed dates or counts")
    expected = options.groupby(option_dates).size().sort_index()
    actual = pd.Series(count_values.to_numpy(), index=count_dates).groupby(level=0).sum().sort_index()
    if not expected.equals(actual.astype(expected.dtype)):
        raise ValueError(f"{ticker} count CSV does not match option rows")

    return {
        "option_rows": len(options),
        "price_rows": len(prices),
        "newest_option_date": option_dates.max().strftime("%Y-%m-%d"),
        "newest_price_date": price_dates.max().strftime("%Y-%m-%d"),
    }


def validate_all_tickers(
    tickers: list[str],
    csv_dir: str | Path = "data/csv",
    price_dir: str | Path = "data/prices",
) -> tuple[dict[str, dict[str, int | str]], dict[str, str]]:
    valid: dict[str, dict[str, int | str]] = {}
    failures: dict[str, str] = {}
    for ticker in tickers:
        try:
            valid[ticker] = validate_ticker_staging(ticker, csv_dir, price_dir)
        except Exception as exc:
            failures[ticker] = str(exc)
    return valid, failures
