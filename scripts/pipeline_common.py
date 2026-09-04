from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, TypeVar


T = TypeVar("T")
RETRY_DELAYS = (2.0, 4.0, 8.0)


class PipelineOperationError(RuntimeError):
    def __init__(self, ticker: str, operation: str, attempts: int, final_exception: Exception):
        self.ticker = ticker
        self.operation = operation
        self.attempts = attempts
        self.final_exception = final_exception
        super().__init__(
            f"ticker={ticker} operation={operation} attempts={attempts} "
            f"final_exception={type(final_exception).__name__}: {final_exception}"
        )


def retry_operation(
    ticker: str,
    operation: str,
    call: Callable[[], T],
    *,
    validate: Callable[[T], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    randomness: Callable[[], float] = random.random,
    on_retry: Callable[[str, str, int, Exception], None] | None = None,
) -> T:
    """Run a network operation four times with 2/4/8s backoff and <=1s jitter."""
    attempts = len(RETRY_DELAYS) + 1
    final_exception: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            result = call()
            if validate is not None:
                validate(result)
            return result
        except Exception as exc:  # network libraries expose several exception types
            final_exception = exc
            if attempt == attempts:
                break
            if on_retry is not None:
                on_retry(ticker, operation, attempt, exc)
            delay = RETRY_DELAYS[attempt - 1] + min(max(float(randomness()), 0.0), 1.0)
            print(
                f"Retrying ticker={ticker} operation={operation} after attempt={attempt}: "
                f"{exc}; sleeping {delay:.2f}s"
            )
            sleep(delay)

    assert final_exception is not None
    raise PipelineOperationError(ticker, operation, attempts, final_exception) from final_exception


@dataclass
class TickerStatus:
    state: str = "pending"
    option_rows: int = 0
    price_rows: int = 0
    newest_option_date: str | None = None
    newest_price_date: str | None = None
    retry_counts: dict[str, int] = field(default_factory=dict)
    error: str | None = None


class PipelineStatus:
    def __init__(self, tickers: list[str]):
        self.tickers = {ticker: TickerStatus() for ticker in tickers}

    def record_retry(self, ticker: str, operation: str, _attempt: int, _exc: Exception) -> None:
        status = self.tickers.get(ticker)
        if status is None:
            return
        status.retry_counts[operation] = status.retry_counts.get(operation, 0) + 1

    def write(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "schema_version": 1,
            "scope": "csv_staging_and_publication",
            "success": all(status.state == "success" for status in self.tickers.values()),
            "tickers": {ticker: asdict(status) for ticker, status in self.tickers.items()},
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
