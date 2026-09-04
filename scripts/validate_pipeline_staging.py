from __future__ import annotations

try:
    from pipeline_validation import validate_all_tickers
    from yf_data_scraper import STOCK_CODES
except ImportError:
    from .pipeline_validation import validate_all_tickers
    from .yf_data_scraper import STOCK_CODES


def main() -> int:
    valid, failures = validate_all_tickers(STOCK_CODES)
    if failures:
        for ticker, error in failures.items():
            print(f"FAILED {ticker}: {error}")
        return 1
    print(f"Validated option, count, and canonical price CSVs for {len(valid)} tickers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
