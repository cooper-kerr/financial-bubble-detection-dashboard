import os
import numpy as np
import pandas as pd
from scipy.io import savemat
from .sbub_lp_easy import sbub_lp_easy
from .sbub_split import sbub_split
from datetime import datetime

def run_mat_generator(stockcode, input_dir, output_dir):
    """
    Runs the MAT file generation process for a single stock.
    Dynamically determines the year range from the input data.
    """
    print(f"--- Starting MAT Generator for {stockcode} ---")

    # Fixed parameters
    pow, nstep, opth, hnumsd = 2, 200, 0, 5

    os.makedirs(output_dir, exist_ok=True)

    # Simplified filenames
    filesource = f"optout_{stockcode}"
    count_file = os.path.join(input_dir, f"{filesource}_count.csv")
    data_file  = os.path.join(input_dir, f"{filesource}.csv")

    if not os.path.exists(count_file) or not os.path.exists(data_file):
        print(f"Input CSV files not found for {stockcode}. Skipping MAT generation.")
        return

    # Dynamically determine year range from count file
    try:
        count_df = pd.read_csv(count_file)
        if count_df.empty:
            print(f"Count file for {stockcode} is empty. Skipping.")
            return
        # Dates are in '%d%b%Y' format
        dates = pd.to_datetime(count_df['date'], format='%d%b%Y')
        yr1 = dates.min().year
        yr2 = dates.max().year
    except (FileNotFoundError, pd.errors.EmptyDataError, KeyError, ValueError) as e:
        print(f"Could not determine year range for {stockcode}. Error: {e}. Skipping.")
        return

    dataname = f"optout_{stockcode}_h{opth}_hsd{hnumsd}_nstep{nstep}"
    matfile = os.path.join(output_dir, dataname + ".mat")

    dataname2 = f"optout_{stockcode}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}"
    splitfile = os.path.join(output_dir, dataname2 + ".mat")

    # Bubble estimation - always re-run to include new data
    print(f"Running bubble estimation for {stockcode}...")
    bubout, dataout, setout = sbub_lp_easy(
        count_file, data_file, pow, nstep, opth, hnumsd
    )

    nperiod = int(setout['nperiod'])
    sout_list = [dataout['sout'][t] for t in range(nperiod)]
    da_list = [dataout['da'][t] for t in range(nperiod)]
    tr_list = [np.array(dataout['tr'][t], float) for t in range(nperiod)]
    op_list = [np.array(dataout['oprice'][t], float) for t in range(nperiod)]
    cp_list = [np.array(dataout['cp'][t], float) for t in range(nperiod)]
    X_list = [np.array(dataout['X'][t], float) for t in range(nperiod)]
    tau_list = [np.array(dataout['tau'][t], float) for t in range(nperiod)]

    dataout_struct = {
        'sout': np.array(sout_list, dtype=float)[None,:],
        'da': np.array(da_list, dtype=float)[None,:],
        'tr': np.array(tr_list, dtype=object)[None,:],
        'oprice': np.array(op_list, dtype=object)[None,:],
        'cp': np.array(cp_list, dtype=object)[None,:],
        'X': np.array(X_list, dtype=object)[None,:],
        'tau': np.array(tau_list, dtype=object)[None,:],
    }

    setout_struct = {k: np.array(v, dtype=float) if isinstance(v, (int, float)) else v for k, v in setout.items()}
    setout_struct['filesource'] = filesource
    setout_struct['yr1'] = str(yr1)
    setout_struct['yr2'] = str(yr2)

    mat_dict = {
        'bubout': bubout,
        'dataout': dataout_struct,
        'setout': setout_struct,
        'stockcode': stockcode,
        'pow': float(pow),
        'nstep': float(nstep),
        'opth': float(opth),
        'hnumsd': float(hnumsd),
    }

    savemat(matfile, mat_dict, do_compression=True)
    print(f"Saved results to {matfile}")

    # Split adjustment - always re-run
    print(f"Running split adjustment for {stockcode}...")
    adjout, _, _ = sbub_split(stockcode, matfile, str(yr1), str(yr2))
    adjout_clean = {key: (value if value is not None else np.array([])) for key, value in adjout.items()}
    savemat(splitfile, {'adjout': adjout_clean}, do_compression=True)
    print(f"Saved split-adjusted results to {splitfile}")

    print(f"--- Finished MAT Generator for {stockcode} ---")
