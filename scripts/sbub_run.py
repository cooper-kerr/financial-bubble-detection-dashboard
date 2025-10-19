import os
import sys
import numpy as np
from scipy.io import savemat
from sbub_lp_easy import sbub_lp_easy
from sbub_split    import sbub_split
import orginal_plot as sbub_plot  # your plotting module
def main():

    # ──────────────── 1) Interactive inputs ────────────────
    default_stock = "SPX"
    default_yr1   = "1996"
    default_yr2   = "2023"

    stockcode = input(f"Enter stock code [{default_stock}]: ").strip() or default_stock
    yr1       = input(f"Enter start year [{default_yr1}]: ").strip()   or default_yr1
    yr2       = input(f"Enter   end year [{default_yr2}]: ").strip()   or default_yr2

    # ──────────────── 2) Fixed parameters ────────────────
    filesource = f"optout_{stockcode}"
    pow, nstep, opth, hnumsd = 2, 200, 0, 5

    output_dir = "/Users/cooperkerr/Desktop/internship/Simulation"
    os.makedirs(output_dir, exist_ok=True)

    # ──────────────── 4) Build filenames ────────────────
    dataname = f"optout_{stockcode}_{yr1}to{yr2}_h{opth}_hsd{hnumsd}_nstep{nstep}"
    matfile = os.path.join(output_dir, dataname + ".mat")
    dataname2 = f"optout_{stockcode}_{yr1}to{yr2}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}"
    splitfile = os.path.join(output_dir, dataname2 + ".mat")

    # ──────────────── 4) Bubble estimation ────────────────
    if os.path.exists(matfile):
        print(f"{matfile} already exists — skipping bubble estimation.")
    else:
        bubout, dataout, setout = sbub_lp_easy(
            filesource, yr1, yr2, pow, nstep, opth, hnumsd
        )

        # build the 7 dataout fields per period
        nperiod   = int(setout['nperiod'])
        sout_list = [ dataout['sout'][t]                     for t in range(nperiod) ]
        da_list   = [ dataout['da'][t]                       for t in range(nperiod) ]
        tr_list   = [ np.array(dataout['tr'][t],    float)   for t in range(nperiod) ]
        op_list   = [ np.array(dataout['oprice'][t],float)   for t in range(nperiod) ]
        cp_list   = [ np.array(dataout['cp'][t],   float)   for t in range(nperiod) ]
        X_list    = [ np.array(dataout['X'][t],    float)   for t in range(nperiod) ]
        tau_list  = [ np.array(dataout['tau'][t],  float)   for t in range(nperiod) ]

        dataout_struct = {
            'sout'   : np.array(sout_list,   dtype=float)[None,:],
            'da'     : np.array(da_list,     dtype=float)[None,:],
            'tr'     : np.array(tr_list,     dtype=object)[None,:],
            'oprice' : np.array(op_list,     dtype=object)[None,:],
            'cp'     : np.array(cp_list,     dtype=object)[None,:],
            'X'      : np.array(X_list,      dtype=object)[None,:],
            'tau'    : np.array(tau_list,    dtype=object)[None,:],
        }

        setout_struct = {
            k: np.array(v, dtype=float) if isinstance(v, (int, float)) else v
            for k, v in setout.items()
        }

        mat_dict = {
            'bubout'    : bubout,
            'dataout'   : dataout_struct,
            'setout'    : setout_struct,
            'stockcode' : stockcode,
            'filesource': filesource,
            'yr1'       : yr1,
            'yr2'       : yr2,
            'pow'       : float(pow),
            'nstep'     : float(nstep),
            'opth'      : float(opth),
            'hnumsd'    : float(hnumsd),
        }

        savemat(matfile, mat_dict)
        print(f"Saved results to {matfile}")

    # ──────────────── 5) Split adjustment ────────────────
    if os.path.exists(splitfile):
        print(f"{splitfile} already exists — skipping split adjustment.")
    else:
        adjout, dataout_split, bubout_split = sbub_split(
            stockcode, matfile, yr1, yr2  # Pass full path
        )

        adjout_clean = {key: (value if value is not None else np.array([])) for key, value in adjout.items()}

        savemat(splitfile, {'adjout': adjout_clean})
        print(f"Saved split‐adjusted results to {splitfile}")
    # ──────────────── 6) Plot ────────────────
    sbub_plot.main()   # calls orginal_plot.main()

if __name__ == "__main__":
    main()

"""
here we need to change to matfile format not npz !!!!!!!!!!!!!!

# ----- SECTION 2: Process for Multiple Stocks -----
stockcodelist = ['SPX', 'AAPL', 'BAC', 'C', 'MSFT', 'FB', 'GE', 'INTC', 'CSCO', 
                 'BABA', 'WFC', 'JPM', 'AMD', 'TWTR', 'F', 'TSLA', 'GOOG', 'T', 
                 'XOM', 'AMZN', 'MS', 'NVDA', 'AIG', 'GM', 'DIS', 'BA']
ns = len(stockcodelist)
yr1 = '1996'
yr2 = '2023'

# Parameters remain the same for all stocks
pow = 2
nstep = 200
opth = 0
hnumsd = 5

for s in range(ns):
    stockcode = stockcodelist[s]
    filesource = "optout_" + stockcode
    dataname = f"optout_{stockcode}_{yr1}to{yr2}_h{opth}_hsd{hnumsd}_nstep{nstep}"
    dataname2 = f"optout_{stockcode}_{yr1}to{yr2}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}"

    # The following lines (bubble estimation) are commented out in MATLAB.
    # If you want to re-run bubble estimation, uncomment:
    # bubout, dataout, setout = sbub_lp_easy(filesource, yr1, yr2, pow, nstep, opth, hnumsd)
    # np.savez(dataname, bubout=bubout, dataout=dataout, setout=setout)
    
    # Handle stock splits:
    # Load the file previously saved (for the specific stock)
    loaded = np.load(dataname + ".npz", allow_pickle=True)
    # Process the stock split adjustment
    adjout = sbub_split(stockcode, dataname, yr1, yr2)
    # Save the adjusted output for this stock
    np.savez(dataname2, adjout=adjout)
"""