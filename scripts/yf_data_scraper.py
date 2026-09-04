from __future__ import annotations

import hashlib
import io
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import pytz
import requests
import yfinance as yf
from fredapi import Fred
from scipy.stats import norm

try:
    from market_calendar import is_us_market_session
    from pipeline_config import STOCK_CODES, YAHOO_SYMBOL_MAP
    from pipeline_common import PipelineStatus, retry_operation
    from pipeline_validation import OPTION_COLUMNS, validate_all_tickers
    from yahoo_csv_utils import merge_sort_option_data, rebuild_count_frame
except ImportError:
    from .market_calendar import is_us_market_session
    from .pipeline_config import STOCK_CODES, YAHOO_SYMBOL_MAP
    from .pipeline_common import PipelineStatus, retry_operation
    from .pipeline_validation import OPTION_COLUMNS, validate_all_tickers
    from .yahoo_csv_utils import merge_sort_option_data, rebuild_count_frame


ROOT_DIR = Path(__file__).resolve().parent.parent
BLOB_CSV_UPLOADER = ROOT_DIR / "scripts" / "upload-csv-to-blob.ts"


def to_yahoo_symbol(symbol: str) -> str:
    return YAHOO_SYMBOL_MAP.get(symbol, symbol)


def file_sha256(path: str | Path) -> str | None:
    file_path = Path(path)
    return hashlib.sha256(file_path.read_bytes()).hexdigest() if file_path.exists() else None


def _require_nonempty(value, label: str) -> None:
    if value is None or not hasattr(value, "empty") or value.empty:
        raise ValueError(f"{label} returned an empty response")


def normalize_price_history(history: pd.DataFrame, ticker: str, yahoo_symbol: str) -> pd.DataFrame:
    _require_nonempty(history, f"Yahoo history for {ticker}")
    frame = history.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        if yahoo_symbol in frame.columns.get_level_values(-1):
            frame = frame.xs(yahoo_symbol, axis=1, level=-1)
        else:
            frame.columns = frame.columns.get_level_values(0)
    frame = frame.reset_index()
    date_column = "Date" if "Date" in frame.columns else frame.columns[0]
    if "Close" not in frame.columns:
        raise ValueError(f"Yahoo history for {ticker} is missing Close")
    regular = pd.to_numeric(frame["Close"], errors="coerce")
    adjusted = pd.to_numeric(frame["Adj Close"], errors="coerce") if "Adj Close" in frame.columns else regular.copy()
    dates = pd.to_datetime(frame[date_column], errors="coerce", utc=True).dt.tz_localize(None)
    normalized = pd.DataFrame({"date": dates, "regular": regular, "adjusted": adjusted})
    normalized = normalized.replace([np.inf, -np.inf], np.nan).dropna()
    normalized = normalized.drop_duplicates("date", keep="last").sort_values("date")
    if normalized.empty:
        raise ValueError(f"Yahoo history for {ticker} has no finite close prices")
    return normalized.reset_index(drop=True)


def fetch_price_history(
    ticker: str,
    start_date: str,
    end_date: str,
    *,
    download: Callable = yf.download,
    sleep: Callable[[float], None] = time.sleep,
    randomness: Callable[[], float] = random.random,
    on_retry: Callable | None = None,
) -> pd.DataFrame:
    yahoo_symbol = to_yahoo_symbol(ticker)
    history = retry_operation(
        ticker,
        "yahoo_history",
        lambda: download(yahoo_symbol, start=start_date, end=end_date, auto_adjust=False, actions=True, progress=False),
        validate=lambda value: normalize_price_history(value, ticker, yahoo_symbol),
        sleep=sleep,
        randomness=randomness,
        on_retry=on_retry,
    )
    return normalize_price_history(history, ticker, yahoo_symbol)


def fetch_fred_series(
    fred,
    start_date: str,
    end_date: str,
    *,
    sleep: Callable[[float], None] = time.sleep,
    randomness: Callable[[], float] = random.random,
    on_retry: Callable | None = None,
) -> pd.DataFrame:
    def normalize(series) -> pd.DataFrame:
        _require_nonempty(series, "FRED DGS1MO")
        frame = pd.DataFrame(series, columns=["tr"]).reset_index()
        frame.columns = ["date", "tr"]
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.tz_localize(None)
        frame["tr"] = pd.to_numeric(frame["tr"], errors="coerce") / 100
        frame = frame.dropna(subset=["date", "tr"]).sort_values("date")
        if frame.empty:
            raise ValueError("FRED DGS1MO contained no parseable observations")
        return frame

    series = retry_operation(
        "ALL",
        "fred_DGS1MO",
        lambda: fred.get_series("DGS1MO", start_date, end_date),
        validate=normalize,
        sleep=sleep,
        randomness=randomness,
        on_retry=on_retry,
    )
    return normalize(series)


def fetch_expirations(ticker: str, yahoo_ticker, *, sleep=time.sleep, randomness=random.random, on_retry=None) -> tuple[str, ...]:
    def validate(expirations) -> None:
        if not expirations:
            raise ValueError(f"Yahoo expirations for {ticker} were empty")
        for value in expirations:
            datetime.strptime(value, "%Y-%m-%d")

    result = retry_operation(
        ticker,
        "yahoo_expirations",
        lambda: yahoo_ticker.options,
        validate=validate,
        sleep=sleep,
        randomness=randomness,
        on_retry=on_retry,
    )
    return tuple(result)


def fetch_option_chain(ticker: str, yahoo_ticker, expiration: str, *, sleep=time.sleep, randomness=random.random, on_retry=None):
    def validate(chain) -> None:
        if chain is None or not hasattr(chain, "calls") or not hasattr(chain, "puts"):
            raise ValueError("malformed option-chain response")
        if chain.calls.empty or chain.puts.empty:
            raise ValueError("option-chain response lacks calls or puts")
        required = {"lastTradeDate", "strike", "bid", "ask", "volume", "openInterest", "impliedVolatility"}
        for label, frame in (("calls", chain.calls), ("puts", chain.puts)):
            missing = sorted(required - set(frame.columns))
            if missing:
                raise ValueError(f"option-chain {label} missing columns: {missing}")
            parsed_dates = pd.to_datetime(frame["lastTradeDate"], errors="coerce", utc=True)
            numeric = frame[["strike", "bid", "ask", "impliedVolatility"]].apply(
                pd.to_numeric, errors="coerce"
            )
            usable = parsed_dates.notna() & np.isfinite(numeric).all(axis=1)
            if not usable.any():
                raise ValueError(f"option-chain {label} has no parseable, finite rows")

    return retry_operation(
        ticker,
        f"yahoo_option_chain:{expiration}",
        lambda: yahoo_ticker.option_chain(expiration),
        validate=validate,
        sleep=sleep,
        randomness=randomness,
        on_retry=on_retry,
    )


def download_csv_from_blob(
    ticker: str,
    blob_path: str,
    local_path: str | Path,
    *,
    base_url: str,
    get: Callable = requests.get,
    sleep=time.sleep,
    randomness=random.random,
    on_retry=None,
) -> None:
    if not base_url:
        raise EnvironmentError("BLOB_BASE_URL environment variable is not set")

    def download() -> bytes:
        response = get(f"{base_url.rstrip('/')}/{blob_path}", timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")
        if not response.content or not response.content.strip():
            raise ValueError("Blob returned an empty CSV")
        parsed = pd.read_csv(io.BytesIO(response.content))
        if parsed.empty:
            raise ValueError("Blob returned a CSV with no data rows")
        missing = sorted(OPTION_COLUMNS - set(parsed.columns))
        if missing:
            raise ValueError(f"Blob option CSV missing columns: {missing}")
        return response.content

    content = retry_operation(
        ticker,
        f"blob_download:{blob_path}",
        download,
        sleep=sleep,
        randomness=randomness,
        on_retry=on_retry,
    )
    output = Path(local_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)
    print(f"Downloaded {blob_path} from Blob")


def upload_csv_to_blob(
    ticker: str,
    local_path: str | Path,
    blob_path: str,
    *,
    token: str,
    run: Callable = subprocess.run,
    sleep=time.sleep,
    randomness=random.random,
    on_retry=None,
) -> None:
    if not token:
        raise EnvironmentError("BLOB_READ_WRITE_TOKEN environment variable is not set")
    tsx_bin = ROOT_DIR / "node_modules" / ".bin" / "tsx"
    command = (
        [str(tsx_bin), str(BLOB_CSV_UPLOADER), str(local_path), blob_path]
        if tsx_bin.exists()
        else ["npx", "tsx", str(BLOB_CSV_UPLOADER), str(local_path), blob_path]
    )

    def upload() -> None:
        result = run(command, text=True, capture_output=True, timeout=120, cwd=ROOT_DIR)
        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"Blob upload failed: {error}")
        if not result.stdout.strip():
            raise ValueError("Blob upload returned no destination URL")
        print(f"Uploaded {local_path} -> {result.stdout.strip()}")

    retry_operation(
        ticker,
        f"blob_upload:{blob_path}",
        upload,
        sleep=sleep,
        randomness=randomness,
        on_retry=on_retry,
    )


def _classify_maturity_group(tau_years: float) -> str:
    if tau_years <= 0.25:
        return "0-3M"
    if tau_years <= 0.5:
        return "3-6M"
    return "6-12M"


def _calculate_delta(row: pd.Series) -> float:
    values = [row["price"], row["strike"], row["tau_years"], row["impliedVolatility"], row["tr"]]
    if any(pd.isna(value) for value in values) or row["tau_years"] <= 0 or row["impliedVolatility"] <= 0:
        return np.nan
    d1 = (
        np.log(row["price"] / row["strike"])
        + (row["tr"] + 0.5 * row["impliedVolatility"] ** 2) * row["tau_years"]
    ) / (row["impliedVolatility"] * np.sqrt(row["tau_years"]))
    return norm.cdf(d1) if row["cp_flag"] == "C" else norm.cdf(d1) - 1


def build_current_option_rows(
    ticker: str,
    price_history: pd.DataFrame,
    fred_data: pd.DataFrame,
    yahoo_ticker,
    now: datetime,
    *,
    sleep=time.sleep,
    randomness=random.random,
    on_retry=None,
) -> pd.DataFrame:
    expirations = fetch_expirations(ticker, yahoo_ticker, sleep=sleep, randomness=randomness, on_retry=on_retry)
    now_naive = now.replace(tzinfo=None)
    eligible = [
        value for value in expirations
        if now_naive <= datetime.strptime(value, "%Y-%m-%d") <= now_naive + timedelta(days=365)
    ]
    if not eligible:
        raise ValueError(f"Yahoo returned no expirations within 365 days for {ticker}")

    frames: list[pd.DataFrame] = []
    for expiration in eligible:
        chain = fetch_option_chain(
            ticker, yahoo_ticker, expiration, sleep=sleep, randomness=randomness, on_retry=on_retry
        )
        for values, flag in ((chain.calls, "C"), (chain.puts, "P")):
            frame = values.copy()
            frame["exdate"] = pd.to_datetime(expiration)
            frame["cp_flag"] = flag
            frames.append(frame)

    options = pd.concat(frames, ignore_index=True).rename(columns={"lastTradeDate": "date"})
    columns = ["date", "exdate", "cp_flag", "strike", "bid", "ask", "volume", "openInterest", "impliedVolatility"]
    missing = sorted(set(columns) - set(options.columns))
    if missing:
        raise ValueError(f"Yahoo option chains for {ticker} missing columns: {missing}")
    options = options[columns].copy()
    options["date"] = pd.to_datetime(options["date"], errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    options["exdate"] = pd.to_datetime(options["exdate"], errors="coerce").dt.tz_localize(None)
    numeric_columns = ["strike", "bid", "ask", "volume", "openInterest", "impliedVolatility"]
    options[numeric_columns] = options[numeric_columns].apply(pd.to_numeric, errors="coerce")
    options["callprice"] = (options["bid"] + options["ask"]) / 2
    options = options.dropna(subset=["date", "exdate", "strike", "callprice", "volume"])
    options["strike"] = options["strike"] / 1000
    options = options[(options["volume"] > 0) & ((options["bid"] >= 0.05) | (options["ask"] >= 0.05))]
    options["tau"] = (options["exdate"] - options["date"]).dt.days
    options = options[(options["tau"] > 8) & (options["tau"] <= 365)]
    options["tau_years"] = options["tau"] / 365
    options["maturity_group"] = options["tau_years"].apply(_classify_maturity_group)
    group_counts = options.groupby(["date", "cp_flag", "maturity_group"]).size().reset_index(name="n_obs")
    options = options.merge(group_counts[group_counts["n_obs"] >= 3][["date", "cp_flag", "maturity_group"]])
    strike_counts = options.groupby(["date", "cp_flag", "tau"])["strike"].nunique().reset_index(name="n_strikes")
    options = options.merge(strike_counts[strike_counts["n_strikes"] >= 2][["date", "cp_flag", "tau"]])

    clean = options.groupby(["date", "cp_flag", "tau", "strike"], as_index=False).agg(
        exdate=("exdate", "max"),
        callprice=("callprice", lambda values: np.average(values, weights=options.loc[values.index, "volume"])),
        volume=("volume", "sum"),
        impliedVolatility=("impliedVolatility", "mean"),
    )
    market = price_history.rename(columns={"regular": "price"})[["date", "price"]]
    market = market.merge(fred_data, on="date", how="left").sort_values("date")
    market["tr"] = market["tr"].ffill()
    combined = clean.merge(market, on="date", how="inner").dropna(subset=["tr"])
    combined["money"] = np.log(combined["strike"] * np.exp(-combined["tr"] * combined["tau"] / 252) / combined["price"])
    combined["tau_years"] = combined["tau"] / 365
    combined["strike"] = combined["strike"] * 1000
    combined["delta"] = combined.apply(_calculate_delta, axis=1)
    combined["date"] = combined["date"].dt.strftime("%d%b%Y")
    combined["exdate"] = combined["exdate"].dt.strftime("%d%b%Y")
    combined = combined.rename(columns={
        "date": "dateraw", "exdate": "exdateraw", "tau": "tauday", "strike": "x",
        "price": "s", "callprice": "oprice", "impliedVolatility": "iv", "delta": "deltachk",
    })
    output_columns = [
        "dateraw", "cp_flag", "exdateraw", "tauday", "x", "s", "tr", "money",
        "oprice", "volume", "iv", "deltachk",
    ]
    today_label = now.strftime("%d%b%Y")
    return combined[combined["dateraw"] == today_label][output_columns].reset_index(drop=True)


def stage_ticker(
    ticker: str,
    fred_data: pd.DataFrame,
    now: datetime,
    *,
    csv_dir: Path,
    price_dir: Path,
    base_url: str,
    download,
    ticker_factory,
    get,
    sleep,
    randomness,
    on_retry,
) -> bool:
    prices = fetch_price_history(
        ticker,
        "1996-01-01",
        (now + timedelta(days=1)).strftime("%Y-%m-%d"),
        download=download,
        sleep=sleep,
        randomness=randomness,
        on_retry=on_retry,
    )
    price_dir.mkdir(parents=True, exist_ok=True)
    price_output = prices.copy()
    price_output["date"] = price_output["date"].dt.strftime("%Y-%m-%d")
    price_output.to_csv(price_dir / f"{ticker}.csv", index=False)
    current_rows = build_current_option_rows(
        ticker,
        prices,
        fred_data,
        ticker_factory(to_yahoo_symbol(ticker)),
        now,
        sleep=sleep,
        randomness=randomness,
        on_retry=on_retry,
    )
    today_date = now.astimezone(pytz.timezone("US/Eastern")).date() if now.tzinfo else now.date()
    today = pd.Timestamp(today_date)
    if is_us_market_session(today_date) and today not in set(prices["date"]):
        newest = prices["date"].max().strftime("%Y-%m-%d")
        raise ValueError(
            f"Yahoo price history for {ticker} is stale on active market date {today_date}: newest={newest}"
        )
    if current_rows.empty and is_us_market_session(today_date):
        raise ValueError(
            f"Yahoo returned no usable current-day option rows for {ticker} on an active price date"
        )

    csv_dir.mkdir(parents=True, exist_ok=True)
    data_path = csv_dir / f"optout_{ticker}.csv"
    if not data_path.exists():
        download_csv_from_blob(
            ticker,
            f"csv/optout_{ticker}.csv",
            data_path,
            base_url=base_url,
            get=get,
            sleep=sleep,
            randomness=randomness,
            on_retry=on_retry,
        )
    before_hash = file_sha256(data_path)
    merged = merge_sort_option_data(pd.read_csv(data_path), current_rows)
    merged.to_csv(data_path, index=False)
    rebuild_count_frame(merged).to_csv(csv_dir / f"optout_{ticker}_count.csv", index=False)
    return before_hash != file_sha256(data_path)


def run_pipeline(
    *,
    tickers: list[str] = STOCK_CODES,
    csv_dir: str | Path = "data/csv",
    price_dir: str | Path = "data/prices",
    status_path: str | Path = "data/pipeline-status.json",
    now: datetime | None = None,
    download: Callable = yf.download,
    ticker_factory: Callable = yf.Ticker,
    fred_factory: Callable = Fred,
    get: Callable = requests.get,
    run: Callable = subprocess.run,
    sleep: Callable[[float], None] = time.sleep,
    randomness: Callable[[], float] = random.random,
) -> int:
    statuses = PipelineStatus(tickers)
    csv_path, price_path = Path(csv_dir), Path(price_dir)
    changed: dict[str, bool] = {}
    current_time = now or datetime.now(pytz.timezone("US/Eastern"))

    def fred_retry(_ticker, operation, attempt, exc):
        for configured_ticker in tickers:
            statuses.record_retry(configured_ticker, operation, attempt, exc)

    try:
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            raise EnvironmentError("FRED_API_KEY environment variable is not set")
        fred_data = fetch_fred_series(
            fred_factory(api_key=api_key),
            "1996-01-01",
            (current_time + timedelta(days=1)).strftime("%Y-%m-%d"),
            sleep=sleep,
            randomness=randomness,
            on_retry=fred_retry,
        )
    except Exception as exc:
        for status in statuses.tickers.values():
            status.state, status.error = "failed", str(exc)
        statuses.write(status_path)
        print(f"Pipeline failed before ticker staging: {exc}", file=sys.stderr)
        return 1

    for ticker in tickers:
        print(f"Staging {ticker}...")
        try:
            changed[ticker] = stage_ticker(
                ticker,
                fred_data,
                current_time,
                csv_dir=csv_path,
                price_dir=price_path,
                base_url=os.getenv("BLOB_BASE_URL", ""),
                download=download,
                ticker_factory=ticker_factory,
                get=get,
                sleep=sleep,
                randomness=randomness,
                on_retry=statuses.record_retry,
            )
            statuses.tickers[ticker].state = "staged"
        except Exception as exc:
            statuses.tickers[ticker].state, statuses.tickers[ticker].error = "failed", str(exc)
            print(f"FAILED {ticker}: {exc}", file=sys.stderr)

    valid, validation_failures = validate_all_tickers(tickers, csv_path, price_path)
    for ticker, details in valid.items():
        status = statuses.tickers[ticker]
        status.option_rows = int(details["option_rows"])
        status.price_rows = int(details["price_rows"])
        status.newest_option_date = str(details["newest_option_date"])
        status.newest_price_date = str(details["newest_price_date"])
    for ticker, error in validation_failures.items():
        statuses.tickers[ticker].state, statuses.tickers[ticker].error = "failed", error

    failed = [ticker for ticker, status in statuses.tickers.items() if status.state == "failed"]
    if failed:
        statuses.write(status_path)
        print(f"Staging validation failed for {len(failed)} ticker(s): {', '.join(failed)}", file=sys.stderr)
        return 1

    token = os.getenv("BLOB_READ_WRITE_TOKEN", "")
    for index, ticker in enumerate(tickers):
        try:
            if changed[ticker]:
                upload_csv_to_blob(
                    ticker,
                    csv_path / f"optout_{ticker}.csv",
                    f"csv/optout_{ticker}.csv",
                    token=token,
                    run=run,
                    sleep=sleep,
                    randomness=randomness,
                    on_retry=statuses.record_retry,
                )
            statuses.tickers[ticker].state = "success"
        except Exception as exc:
            statuses.tickers[ticker].state, statuses.tickers[ticker].error = "failed", str(exc)
            for remaining in tickers[index + 1 :]:
                statuses.tickers[remaining].state = "failed"
                statuses.tickers[remaining].error = "upload skipped after an earlier upload failure"
            statuses.write(status_path)
            print(f"FAILED {ticker}: {exc}", file=sys.stderr)
            return 1

    statuses.write(status_path)
    print(f"Successfully staged, validated, and published {len(tickers)} tickers")
    return 0


def main() -> int:
    return run_pipeline()


if __name__ == "__main__":
    raise SystemExit(main())
