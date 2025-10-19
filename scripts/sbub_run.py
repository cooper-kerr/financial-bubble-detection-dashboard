import os
import numpy as np
from scipy.io import savemat
from sbub_lp_easy import sbub_lp_easy
from sbub_split import sbub_split

def main():
    # ──────────────── 1) Setup ────────────────
    stockcodelist = [
        'SPX', 'AAPL', 'BAC', 'C', 'MSFT', 'FB', 'GE', 'INTC', 'CSCO',
        'BABA', 'WFC', 'JPM', 'AMD', 'TWTR', 'F', 'TSLA', 'GOOG', 'T',
        'XOM', 'AMZN', 'MS', 'NVDA', 'AIG', 'GM', 'DIS', 'BA'
    ]

    yr1, yr2 = '1996', '2025'
    pow_val, nstep, opth, hnumsd = 2, 200, 0, 5

    output_dir = "data/mat"
    os.makedirs(output_dir, exist_ok=True)

    # ──────────────── 2) Loop through stocks ────────────────
    for i, stockcode in enumerate(stockcodelist, 1):
        print(f"\n==================================================")
        print(f"[{i}/{len(stockcodelist)}] Processing {stockcode}...")
        print(f"==================================================")

        filesource = f"optout_{stockcode}"
        dataname = f"{filesource}_{yr1}to{yr2}_h{opth}_hsd{hnumsd}_nstep{nstep}"
        dataname2 = f"{filesource}_{yr1}to{yr2}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}"

        matfile = os.path.join(output_dir, dataname + ".mat")
        splitfile = os.path.join(output_dir, dataname2 + ".mat")

        # ──────────────── 3) Skip if files already exist ────────────────
        if os.path.exists(matfile) and os.path.exists(splitfile):
            print(f"✅ Both {matfile} and {splitfile} already exist — skipping.")
            continue

        # ──────────────── 4) Bubble Estimation ────────────────
        if not os.path.exists(matfile):
            print(f"Running bubble estimation for {stockcode}...")
            try:
                bubout, dataout, setout = sbub_lp_easy(
                    filesource, yr1, yr2, pow_val, nstep, opth, hnumsd
                )

                nperiod = int(setout['nperiod'])
                dataout_struct = {
                    'sout': np.array([dataout['sout'][t] for t in range(nperiod)], dtype=float)[None, :],
                    'da': np.array([dataout['da'][t] for t in range(nperiod)], dtype=float)[None, :],
                    'tr': np.array([np.array(dataout['tr'][t], float) for t in range(nperiod)], dtype=object)[None, :],
                    'oprice': np.array([np.array(dataout['oprice'][t], float) for t in range(nperiod)], dtype=object)[None, :],
                    'cp': np.array([np.array(dataout['cp'][t], float) for t in range(nperiod)], dtype=object)[None, :],
                    'X': np.array([np.array(dataout['X'][t], float) for t in range(nperiod)], dtype=object)[None, :],
                    'tau': np.array([np.array(dataout['tau'][t], float) for t in range(nperiod)], dtype=object)[None, :],
                }

                setout_struct = {
                    k: np.array(v, dtype=float) if isinstance(v, (int, float)) else v
                    for k, v in setout.items()
                }

                mat_dict = {
                    'bubout': bubout,
                    'dataout': dataout_struct,
                    'setout': setout_struct,
                    'stockcode': stockcode,
                    'filesource': filesource,
                    'yr1': yr1,
                    'yr2': yr2,
                    'pow': float(pow_val),
                    'nstep': float(nstep),
                    'opth': float(opth),
                    'hnumsd': float(hnumsd),
                }

                savemat(matfile, mat_dict)
                print(f"💾 Saved bubble estimation results to {matfile}")
            except Exception as e:
                print(f"❌ Error processing {stockcode} during bubble estimation: {e}")
                continue

        # ──────────────── 5) Split Adjustment ────────────────
        if not os.path.exists(splitfile):
            print(f"Applying split adjustment for {stockcode}...")
            try:
                adjout, dataout_split, bubout_split = sbub_split(
                    stockcode, matfile, yr1, yr2
                )

                adjout_clean = {
                    key: (value if value is not None else np.array([]))
                    for key, value in adjout.items()
                }

                savemat(splitfile, {'adjout': adjout_clean})
                print(f"💾 Saved split-adjusted results to {splitfile}")
            except Exception as e:
                print(f"❌ Error during split adjustment for {stockcode}: {e}")

    print("\n==================================================")
    print("✅ All MAT file conversions complete.")
    print("==================================================")


if __name__ == "__main__":
    main()

