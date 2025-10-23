import os
import numpy as np
import pandas as pd
from scipy.io import savemat
from sbub_lp_easy import sbub_lp_easy
from sbub_split import sbub_split

def main():
    # ──────────────── Ticker list ────────────────
    stockcodelist = ['AAPL', 'AIG', 'AMD', 'AMZN', 'BA', 'BABA', 'BAC', 'C', 'CSCO',
                     'DIS', 'F', 'GE', 'GM', 'GOOG', 'INTC', 'JPM', 'META', 'MS', 
                     'MSFT', 'NVDA', 'T', 'TSLA', 'WFC', 'XOM', '^SPX']

    # ──────────────── Parameters ────────────────
    yr1, yr2 = '2025', '2025'
    
    pow, nstep, opth, hnumsd = 2, 200, 0, 5

    output_dir = "data/mat"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Found {len(stockcodelist)} tickers to process: {', '.join(stockcodelist)}\n")

    for idx, stockcode in enumerate(stockcodelist, 1):
        print("="*50)
        print(f"[{idx}/{len(stockcodelist)}] Processing {stockcode}...")
        print("="*50)

        try:
            # Build CSV paths for this ticker
            data_file  = f"data/csv/optout_{stockcode}.csv"
            count_file = f"data/csv/optout_{stockcode}_count.csv"

            # Build MAT filenames
            dataname  = f"optout_{stockcode}_{yr1}to{yr2}_h{opth}_hsd{hnumsd}_nstep{nstep}"
            dataname  = f"optout_{stockcode}_to_h{opth}_hsd{hnumsd}_nstep{nstep}"
            matfile   = os.path.join(output_dir, dataname + ".mat")
            dataname2 = f"optout_{stockcode}_{yr1}to{yr2}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}"
            dataname2 = f"optout_{stockcode}_to_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}"
            splitfile = os.path.join(output_dir, dataname2 + ".mat")

            # ──────────────── Bubble estimation ────────────────
            print(f"Running bubble estimation for {stockcode}...")
            bubout, dataout, setout = sbub_lp_easy(
                data_file,
                count_file,
                yr1,
                yr2,
                pow,
                nstep,
                opth,
                hnumsd
            )

            # Build dataout_struct
            nperiod = int(setout['nperiod'])
            dataout_struct = {
                'sout'   : np.array([dataout['sout'][t] for t in range(nperiod)], dtype=float)[None,:],
                'da'     : np.array([dataout['da'][t]   for t in range(nperiod)], dtype=float)[None,:],
                'tr'     : np.array([np.array(dataout['tr'][t], float)    for t in range(nperiod)], dtype=object)[None,:],
                'oprice' : np.array([np.array(dataout['oprice'][t], float) for t in range(nperiod)], dtype=object)[None,:],
                'cp'     : np.array([np.array(dataout['cp'][t], float)    for t in range(nperiod)], dtype=object)[None,:],
                'X'      : np.array([np.array(dataout['X'][t], float)     for t in range(nperiod)], dtype=object)[None,:],
                'tau'    : np.array([np.array(dataout['tau'][t], float)   for t in range(nperiod)], dtype=object)[None,:],
            }

            setout_struct = {k: np.array(v, dtype=float) if isinstance(v, (int,float)) else v
                             for k,v in setout.items()}

            # Save MAT file
            mat_dict = {
                'bubout'    : bubout,
                'dataout'   : dataout_struct,
                'setout'    : setout_struct,
                'stockcode' : stockcode,
                'filesource': f"optout_{stockcode}",
                'yr1'       : yr1,
                'yr2'       : yr2,
                'pow'       : float(pow),
                'nstep'     : float(nstep),
                'opth'      : float(opth),
                'hnumsd'    : float(hnumsd),
            }
            savemat(matfile, mat_dict)
            print(f"✅ Saved bubble results to {matfile}")

            # ──────────────── Split adjustment ────────────────
            print(f"Running split adjustment for {stockcode}...")
            adjout, dataout_split, bubout_split = sbub_split(stockcode, matfile, yr1, yr2)
            adjout, dataout_split, bubout_split = sbub_split(stockcode, matfile)
            adjout_clean = {k: (v if v is not None else np.array([])) for k,v in adjout.items()}
            savemat(splitfile, {'adjout': adjout_clean})
            print(f"✅ Saved split-adjusted results to {splitfile}\n")

        except Exception as e:
            print(f"❌ Error processing {stockcode} during bubble estimation: {e}\n")
            continue

if __name__ == "__main__":
    main()
