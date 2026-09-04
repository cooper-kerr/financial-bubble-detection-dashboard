from __future__ import annotations

import os
from datetime import datetime

import numpy as np
from scipy.io import savemat

try:
    from pipeline_config import STOCK_CODES
    from pipeline_validation import validate_all_tickers
    from sbub_lp_easy import sbub_lp_easy
    from sbub_split import sbub_split
except ImportError:
    from .pipeline_config import STOCK_CODES
    from .pipeline_validation import validate_all_tickers
    from .sbub_lp_easy import sbub_lp_easy
    from .sbub_split import sbub_split


def process_stock(stockcode: str, csv_dir: str, output_dir: str, current_year: int) -> None:
    yr1, yr2 = "2025", str(current_year)
    power, nstep, opth, hnumsd = 2, 200, 0, 5
    data_file = f"{csv_dir}/optout_{stockcode}.csv"
    count_file = f"{csv_dir}/optout_{stockcode}_count.csv"
    dataname = f"optout_{stockcode}_{yr1}to{yr2}_h{opth}_hsd{hnumsd}_nstep{nstep}"
    matfile = os.path.join(output_dir, dataname + ".mat")
    split_name = f"optout_{stockcode}_{yr1}to{yr2}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}"
    splitfile = os.path.join(output_dir, split_name + ".mat")

    print(f"Running bubble estimation for {stockcode}...")
    bubout, dataout, setout = sbub_lp_easy(
        data_file, count_file, yr1, yr2, power, nstep, opth, hnumsd
    )
    nperiod = int(setout["nperiod"])
    dataout_struct = {
        "sout": np.array([dataout["sout"][t] for t in range(nperiod)], dtype=float)[None, :],
        "da": np.array([dataout["da"][t] for t in range(nperiod)], dtype=float)[None, :],
        "tr": np.array([np.array(dataout["tr"][t], float) for t in range(nperiod)], dtype=object)[None, :],
        "oprice": np.array([np.array(dataout["oprice"][t], float) for t in range(nperiod)], dtype=object)[None, :],
        "cp": np.array([np.array(dataout["cp"][t], float) for t in range(nperiod)], dtype=object)[None, :],
        "X": np.array([np.array(dataout["X"][t], float) for t in range(nperiod)], dtype=object)[None, :],
        "tau": np.array([np.array(dataout["tau"][t], float) for t in range(nperiod)], dtype=object)[None, :],
    }
    setout_struct = {
        key: np.array(value, dtype=float) if isinstance(value, (int, float)) else value
        for key, value in setout.items()
    }
    savemat(
        matfile,
        {
            "bubout": bubout,
            "dataout": dataout_struct,
            "setout": setout_struct,
            "stockcode": stockcode,
            "filesource": f"optout_{stockcode}",
            "yr1": yr1,
            "yr2": yr2,
            "pow": float(power),
            "nstep": float(nstep),
            "opth": float(opth),
            "hnumsd": float(hnumsd),
        },
    )
    print(f"Saved bubble results to {matfile}")

    print(f"Running split adjustment for {stockcode}...")
    adjout, _, _ = sbub_split(stockcode, matfile, yr1, yr2)
    adjout_clean = {key: value if value is not None else np.array([]) for key, value in adjout.items()}
    savemat(splitfile, {"adjout": adjout_clean})
    print(f"Saved split-adjusted results to {splitfile}")


def main() -> int:
    csv_dir = "data/csv"
    output_dir = "data/mat"
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    _, validation_failures = validate_all_tickers(STOCK_CODES, csv_dir, "data/prices")
    if validation_failures:
        print("Staging validation failed; MAT computation will not start:")
        for ticker, error in validation_failures.items():
            print(f"  - {ticker}: {error}")
        return 1

    successful: list[str] = []
    failures: dict[str, str] = {}
    print(f"Found {len(STOCK_CODES)} tickers to process: {', '.join(STOCK_CODES)}")
    for index, stockcode in enumerate(STOCK_CODES, 1):
        print(f"[{index}/{len(STOCK_CODES)}] Processing {stockcode}...")
        try:
            process_stock(stockcode, csv_dir, output_dir, datetime.now().year)
            successful.append(stockcode)
        except Exception as exc:
            failures[stockcode] = str(exc)
            print(f"Error processing {stockcode}: {exc}")

    print(f"MAT summary: {len(successful)} succeeded, {len(failures)} failed")
    for ticker, error in failures.items():
        print(f"  - {ticker}: {error}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
