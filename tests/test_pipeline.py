from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pandas as pd

from scripts import bubble_estimator
from scripts import sbub_run
from scripts.market_calendar import is_us_market_session
from scripts.pipeline_common import PipelineOperationError, retry_operation
from scripts.pipeline_validation import validate_ticker_staging
from scripts import yf_data_scraper as scraper


OPTION_COLUMNS = [
    "dateraw", "cp_flag", "exdateraw", "tauday", "x", "s", "tr", "money",
    "oprice", "volume", "iv", "deltachk",
]


def option_frame(date="02Jan2025"):
    rows = []
    for flag, strike in (("C", 100.0), ("P", 101.0)):
        rows.append([date, flag, "21Feb2025", 50, strike, 100.0, 0.04, 0.0, 2.0, 10, 0.2, 0.5])
    return pd.DataFrame(rows, columns=OPTION_COLUMNS)


class RetryTests(unittest.TestCase):
    def test_transient_success_uses_exponential_delays_and_jitter(self):
        calls = []
        sleeps = []

        def operation():
            calls.append(1)
            if len(calls) < 3:
                raise RuntimeError("temporary")
            return "ok"

        result = retry_operation(
            "AAPL", "test", operation, sleep=sleeps.append, randomness=lambda: 0.5
        )
        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [2.5, 4.5])

    def test_retry_exhaustion_has_structured_error(self):
        with self.assertRaisesRegex(
            PipelineOperationError,
            r"ticker=AAPL operation=yahoo_history attempts=4 final_exception=RuntimeError: down",
        ):
            retry_operation(
                "AAPL", "yahoo_history", lambda: (_ for _ in ()).throw(RuntimeError("down")),
                sleep=lambda _delay: None, randomness=lambda: 0,
            )

    def test_empty_history_retries_then_succeeds(self):
        responses = [pd.DataFrame(), pd.DataFrame({"Date": ["2025-01-02"], "Close": [10.0]})]
        history = scraper.fetch_price_history(
            "AAPL", "2025-01-01", "2025-01-03",
            download=lambda *_args, **_kwargs: responses.pop(0),
            sleep=lambda _delay: None, randomness=lambda: 0,
        )
        self.assertEqual(history["regular"].tolist(), [10.0])

    def test_missing_close_is_retryable_and_exhausts(self):
        calls = []

        def malformed(*_args, **_kwargs):
            calls.append(1)
            return pd.DataFrame({"Date": ["2025-01-02"], "Open": [10.0]})

        with self.assertRaisesRegex(PipelineOperationError, "missing Close"):
            scraper.fetch_price_history(
                "AAPL", "2025-01-01", "2025-01-03", download=malformed,
                sleep=lambda _delay: None, randomness=lambda: 0,
            )
        self.assertEqual(len(calls), 4)

    def test_failed_expiration_chain_exhausts(self):
        empty_chain = SimpleNamespace(calls=pd.DataFrame(), puts=pd.DataFrame())
        yahoo_ticker = SimpleNamespace(option_chain=mock.Mock(return_value=empty_chain))
        with self.assertRaisesRegex(PipelineOperationError, "lacks calls or puts"):
            scraper.fetch_option_chain(
                "AAPL", yahoo_ticker, "2025-02-21",
                sleep=lambda _delay: None, randomness=lambda: 0,
            )
        self.assertEqual(yahoo_ticker.option_chain.call_count, 4)

    def test_numerically_malformed_option_chain_retries(self):
        malformed = pd.DataFrame({
            "lastTradeDate": ["bad"], "strike": [None], "bid": [None], "ask": [None],
            "volume": [None], "openInterest": [None], "impliedVolatility": [None],
        })
        yahoo_ticker = SimpleNamespace(option_chain=mock.Mock(return_value=SimpleNamespace(
            calls=malformed, puts=malformed,
        )))
        with self.assertRaisesRegex(PipelineOperationError, "no parseable, finite"):
            scraper.fetch_option_chain(
                "AAPL", yahoo_ticker, "2025-02-21",
                sleep=lambda _delay: None, randomness=lambda: 0,
            )
        self.assertEqual(yahoo_ticker.option_chain.call_count, 4)

    def test_malformed_fred_response_is_retryable(self):
        fred = SimpleNamespace(get_series=mock.Mock(side_effect=[
            pd.Series(["bad"], index=["not-a-date"]),
            pd.Series([4.0], index=pd.to_datetime(["2025-01-02"])),
        ]))
        sleeps = []
        result = scraper.fetch_fred_series(
            fred, "2025-01-01", "2025-01-03",
            sleep=sleeps.append, randomness=lambda: 0,
        )
        self.assertEqual(fred.get_series.call_count, 2)
        self.assertEqual(sleeps, [2.0])
        self.assertEqual(result["tr"].tolist(), [0.04])


class StagingTests(unittest.TestCase):
    def write_staging(
        self,
        root: Path,
        ticker="AAPL",
        option_date="02Jan2025",
        price_dates=("2025-01-02",),
    ):
        csv_dir, price_dir = root / "csv", root / "prices"
        csv_dir.mkdir()
        price_dir.mkdir()
        options = option_frame(option_date)
        options.to_csv(csv_dir / f"optout_{ticker}.csv", index=False)
        pd.DataFrame({"dateraw": [option_date], "count": [2]}).to_csv(
            csv_dir / f"optout_{ticker}_count.csv", index=False
        )
        pd.DataFrame({
            "date": list(price_dates),
            "regular": [100.0] * len(price_dates),
            "adjusted": [99.0] * len(price_dates),
        }).to_csv(price_dir / f"{ticker}.csv", index=False)
        return csv_dir, price_dir

    def test_missing_canonical_option_date_is_precise(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_dir, price_dir = self.write_staging(Path(temp), price_dates=("2025-01-03",))
            with self.assertRaisesRegex(ValueError, "canonical prices do not cover option dates: \\['2025-01-02'\\]"):
                validate_ticker_staging("AAPL", csv_dir, price_dir)

    def test_holiday_with_no_new_rows_preserves_valid_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            csv_dir, price_dir = self.write_staging(
                root, option_date="03Jul2025", price_dates=("2025-07-03",)
            )
            original = (csv_dir / "optout_AAPL.csv").read_text()
            prices = pd.DataFrame({
                "date": pd.to_datetime(["2025-07-03"]), "regular": [100.0], "adjusted": [99.0]
            })
            with mock.patch.object(scraper, "fetch_price_history", return_value=prices), mock.patch.object(
                scraper, "build_current_option_rows", return_value=pd.DataFrame(columns=OPTION_COLUMNS)
            ):
                changed = scraper.stage_ticker(
                    "AAPL", pd.DataFrame(), datetime(2025, 7, 4),
                    csv_dir=csv_dir, price_dir=price_dir, base_url="unused",
                    download=mock.Mock(), ticker_factory=mock.Mock(), get=mock.Mock(),
                    sleep=lambda _delay: None, randomness=lambda: 0, on_retry=None,
                )
            self.assertFalse(changed)
            self.assertEqual((csv_dir / "optout_AAPL.csv").read_text(), original)
            validate_ticker_staging("AAPL", csv_dir, price_dir)

    def test_stale_history_on_active_market_day_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            csv_dir, price_dir = self.write_staging(root)
            prices = pd.DataFrame({
                "date": pd.to_datetime(["2025-01-02"]), "regular": [100.0], "adjusted": [99.0]
            })
            with mock.patch.object(scraper, "fetch_price_history", return_value=prices), mock.patch.object(
                scraper, "build_current_option_rows", return_value=pd.DataFrame(columns=OPTION_COLUMNS)
            ), self.assertRaisesRegex(ValueError, "stale on active market date 2025-01-03"):
                scraper.stage_ticker(
                    "AAPL", pd.DataFrame(), datetime(2025, 1, 3),
                    csv_dir=csv_dir, price_dir=price_dir, base_url="unused",
                    download=mock.Mock(), ticker_factory=mock.Mock(), get=mock.Mock(),
                    sleep=lambda _delay: None, randomness=lambda: 0, on_retry=None,
                )

    def test_market_calendar_distinguishes_good_friday(self):
        self.assertFalse(is_us_market_session(datetime(2026, 4, 3).date()))
        self.assertTrue(is_us_market_session(datetime(2026, 4, 6).date()))


class OfflineAndBatchTests(unittest.TestCase):
    def test_offline_price_loader_and_missing_date_message(self):
        with tempfile.TemporaryDirectory() as temp:
            price_dir = Path(temp)
            pd.DataFrame({
                "date": ["2025-01-02"], "regular": [100.0], "adjusted": [99.0]
            }).to_csv(price_dir / "AAPL.csv", index=False)
            series, mapping = bubble_estimator.load_canonical_price_series(
                "AAPL", "2025-01-01", "2025-12-31", price_dir
            )
            self.assertEqual(series[0]["regular"], 100.0)
            with self.assertRaisesRegex(ValueError, "bubble date 2025-01-03"):
                bubble_estimator.canonical_price_for_date("AAPL", mapping, "2025-01-03")

    def test_fred_is_fetched_once_for_multi_ticker_run(self):
        fred = SimpleNamespace(get_series=mock.Mock(return_value=pd.Series(
            [4.0], index=pd.to_datetime(["2025-01-02"])
        )))
        validation = {
            ticker: {"option_rows": 2, "price_rows": 1, "newest_option_date": "2025-01-02", "newest_price_date": "2025-01-02"}
            for ticker in ("AAPL", "MSFT")
        }
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ, {"FRED_API_KEY": "test"}), mock.patch.object(
            scraper, "stage_ticker", return_value=False
        ), mock.patch.object(scraper, "validate_all_tickers", return_value=(validation, {})):
            result = scraper.run_pipeline(
                tickers=["AAPL", "MSFT"], status_path=Path(temp) / "status.json",
                fred_factory=lambda **_kwargs: fred, sleep=lambda _delay: None, randomness=lambda: 0,
            )
        self.assertEqual(result, 0)
        self.assertEqual(fred.get_series.call_count, 1)

    def test_scraper_upload_failure_stops_later_uploads_and_marks_status(self):
        fred = SimpleNamespace(get_series=mock.Mock(return_value=pd.Series(
            [4.0], index=pd.to_datetime(["2025-01-02"])
        )))
        validation = {
            ticker: {"option_rows": 2, "price_rows": 1, "newest_option_date": "2025-01-02", "newest_price_date": "2025-01-02"}
            for ticker in ("AAPL", "MSFT")
        }
        upload_error = PipelineOperationError("AAPL", "blob_upload:csv/optout_AAPL.csv", 4, RuntimeError("denied"))
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(
            os.environ, {"FRED_API_KEY": "test", "BLOB_READ_WRITE_TOKEN": "test"}
        ), mock.patch.object(scraper, "stage_ticker", return_value=True), mock.patch.object(
            scraper, "validate_all_tickers", return_value=(validation, {})
        ), mock.patch.object(scraper, "upload_csv_to_blob", side_effect=upload_error) as upload:
            status_path = Path(temp) / "status.json"
            result = scraper.run_pipeline(
                tickers=["AAPL", "MSFT"], status_path=status_path,
                fred_factory=lambda **_kwargs: fred, sleep=lambda _delay: None, randomness=lambda: 0,
            )
            status = json.loads(status_path.read_text())
        self.assertEqual(result, 1)
        self.assertEqual(upload.call_count, 1)
        self.assertEqual(status["scope"], "csv_staging_and_publication")
        self.assertEqual(status["tickers"]["AAPL"]["state"], "failed")
        self.assertEqual(status["tickers"]["MSFT"]["state"], "failed")

    def test_json_batch_returns_nonzero_after_summary(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(
            bubble_estimator, "stockcodelist", ["AAPL", "MSFT"]
        ), mock.patch.object(
            bubble_estimator, "IMG_DIR", Path(temp) / "img"
        ), mock.patch.object(
            bubble_estimator, "DATA_DIR", Path(temp) / "data"
        ), mock.patch.object(
            bubble_estimator, "process_stock", side_effect=[True, RuntimeError("broken")]
        ):
            self.assertEqual(bubble_estimator.main(), 1)

    def test_mat_batch_refuses_incomplete_staging(self):
        with mock.patch.object(
            sbub_run, "validate_all_tickers", return_value=({}, {"AAPL": "missing prices"})
        ), mock.patch.object(sbub_run, "STOCK_CODES", ["AAPL"]):
            self.assertEqual(sbub_run.main(), 1)

    def test_mat_batch_returns_nonzero_after_mid_batch_failure(self):
        validation = {
            ticker: {"option_rows": 2, "price_rows": 1, "newest_option_date": "2025-01-02", "newest_price_date": "2025-01-02"}
            for ticker in ("AAPL", "MSFT")
        }
        with mock.patch.object(
            sbub_run, "validate_all_tickers", return_value=(validation, {})
        ), mock.patch.object(sbub_run, "STOCK_CODES", ["AAPL", "MSFT"]), mock.patch.object(
            sbub_run, "process_stock", side_effect=[None, RuntimeError("estimator failed")]
        ) as process:
            self.assertEqual(sbub_run.main(), 1)
        self.assertEqual(process.call_count, 2)


if __name__ == "__main__":
    unittest.main()
