import os
import sys
import numpy as np
import scipy.io as sio
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date
import pandas as pd
import json
from pathlib import Path
import glob

# Point to the folder containing downloaded .mat files (from artifact)
SCRIPT_DIR = Path(os.environ.get("MAT_ARTIFACT_DIR", "./data/mat")).resolve()

# Output folders
IMG_DIR = Path("data/img")
DATA_DIR = Path("public/data")

IMG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Stock list
stockcodelist = ['SPX', 'AAPL', 'BAC', 'C', 'MSFT', 'FB', 'GE', 'INTC', 'CSCO',
                 'BABA', 'WFC', 'JPM', 'AMD', 'TWTR', 'F', 'TSLA', 'GOOG', 'T',
                 'XOM', 'AMZN', 'MS', 'NVDA', 'AIG', 'GM', 'DIS', 'BA']

# Helper functions (keeping all existing helper functions)
def datenum(date_str, fmt='%d-%b-%Y'):
    return datetime.strptime(date_str, fmt).toordinal() + 366

def matlab_datenum_to_datetime(matlab_datenum):
    return date.fromordinal(int(matlab_datenum) - 366)

def nzmean(x):
    return np.nanmean(x)

def nzsum(x):
    return np.nansum(x)

def nw_cov(q, m):
    mu = np.mean(q)
    n = len(q)
    gam = np.zeros(m)
    cov_val = 0.0
    for j in range(1, m + 1):
        gam[j - 1] = np.sum((q[:n - j] - mu) * (q[j:] - mu)) / n
        cov_val += (1 - j / (m + 1)) * gam[j - 1]
    return cov_val

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(NumpyEncoder, self).default(obj)

def process_stock(stockcode):
    """Process a single stock and generate JSON"""
    print(f"\n{'='*50}")
    print(f"Processing {stockcode}...")
    print(f"{'='*50}")

    current_year = datetime.now().year
    yr1, yr2 = '2025', str(current_year)
    startday = f'01JAN{yr1}'
    endday   = f'31DEC{yr2}'
    nplots = 3

    scode, bubwin0, nstep, opth, hnumsd = stockcode, 63, 200, 0, 5

    # Construct full paths for loading .mat files
    # The files are now expected to be in the same directory as the script
    splitadj_files = list(SCRIPT_DIR.glob(f"optout_{stockcode}_*_splitadj_h0_hsd5_nstep200.mat"))
    if splitadj_files:
        dataname2_path = splitadj_files[0]
        print(f"Using split-adjusted .mat file: {dataname2_path}")
    else:
        print(f"No split-adjusted .mat file found for {stockcode}")
        return False
    
    ref_files = list(SCRIPT_DIR.glob(f"optout_{stockcode}_*_h0_hsd5_nstep200.mat"))
    # exclude the split-adjusted file
    ref_files = [f for f in ref_files if "_splitadj_" not in f.name]
    if ref_files:
        reference_file_path = ref_files[0]
        print(f"Using reference .mat file: {reference_file_path}")
    else:
        print(f"No reference .mat file found for {stockcode}")
        return False

    try:
        # Load the split-adjusted file for adjout
        mat_data = sio.loadmat(dataname2_path, squeeze_me=True)
        adjout = {name: mat_data['adjout'][name].item() if mat_data['adjout'][name].size == 1
                  else mat_data['adjout'][name]
                  for name in mat_data['adjout'].dtype.names}

        # Load the non-split-adjusted file for bubout, setout, dataout
        mat_data1 = sio.loadmat(reference_file_path, squeeze_me=True)
        bubout = {name: mat_data1['bubout'][name].item() if mat_data1['bubout'][name].size == 1
                  else mat_data1['bubout'][name]
                  for name in mat_data1['bubout'].dtype.names}
        setout = {name: mat_data1['setout'][name].item() if mat_data1['setout'][name].size == 1
                  else mat_data1['setout'][name]
                  for name in mat_data1['setout'].dtype.names}
        dataout = {name: mat_data1['dataout'][name].item() if mat_data1['dataout'][name].size == 1
                   else mat_data1['dataout'][name]
                   for name in mat_data1['dataout'].dtype.names}
    except FileNotFoundError:
        print(f"ERROR: One or more .mat files not found for {stockcode} in the script directory: {SCRIPT_DIR}")
        print(f"  Missing: {dataname2_path} or {reference_file_path}")
        return False
    except Exception as e:
        print(f"An error occurred while loading .mat files for {stockcode}: {e}")
        return False

    # Explicitly load tau, cp, and dab from dataout.
    tau = dataout['tau']  # Expecting a NumPy array of 1066 elements
    cp  = dataout['cp']
    dab = dataout['da']

    # Set up tau interval parameters.
    taumu = [0.25, 0.5, 1]
    taulb = np.array([0.15, 0.35, 0.75])
    tauub = np.array([0.35, 0.65, 1.25])
    ntaugp = len(taulb)

    # Load bubble metrics from adjout.
    sbub_qcdfp      = adjout['sbub_qcdfp_adj']
    sbub_qcdfc      = adjout['sbub_qcdfc_adj']
    sbub_qcdf       = adjout['sbub_qcdf_adj']
    sbub_qcdfp_se   = adjout['sbub_qcdfp_se_adj']
    sbub_qcdfc_se   = adjout['sbub_qcdfc_se_adj']
    sbub_qcdf_se    = adjout['sbub_qcdf_se_adj']
    qcdfp_bias      = adjout['qcdfp_bias_adj']
    qcdfc_bias      = adjout['qcdfc_bias_adj']
    qcdf_bias       = adjout['qcdf_bias_adj']
    qcdf_A_lb       = adjout['qcdf_A_lb_adj']
    qcdf_A_ub       = adjout['qcdf_A_ub_adj']
    qcdf_Ap_lb      = adjout['qcdf_Ap_lb_adj']
    qcdf_Ap_ub      = adjout['qcdf_Ap_ub_adj']
    qcdf_Ac_lb      = adjout['qcdf_Ac_lb_adj']
    qcdf_Ac_ub      = adjout['qcdf_Ac_ub_adj']

    # Also from bubout:
    scene    = bubout['scene']
    qcdfp_lb = bubout['qcdfp_lb']
    qcdfp_ub = bubout['qcdfp_ub']
    qcdfc_lb = bubout['qcdfc_lb']
    qcdfc_ub = bubout['qcdfc_ub']

    nperiod = int(setout['nperiod'])

    # Split-adjusted data.
    sout = adjout['sout_adj']

    # Set thresholds.
    qmax, semax = 1000, 1000

    # Impute "non-sensible" values for standard errors.
    sbub_qcdf_se    = np.real(sbub_qcdf_se)
    sbub_qcdfp_se   = np.real(sbub_qcdfp_se)
    sbub_qcdfc_se   = np.real(sbub_qcdfc_se)

    # Determine the number of tau columns.
    ntau = sbub_qcdf.shape[1]

    # ============================
    # Filter dates - CORRECTED DATE CONVERSION
    # Convert MATLAB datenum directly to ordinal (no -366 adjustment needed here)
    dab_numeric = np.array([int(d) for d in dab])

    # Convert startday and endday to MATLAB datenum format for comparison
    st_date = pd.to_datetime(startday, format="%d%b%Y")
    end_date = pd.to_datetime(endday, format="%d%b%Y")

    # Convert to MATLAB datenum (adding 366 to match MATLAB's datenum)
    st_dn = st_date.toordinal() + 366
    end_dn = end_date.toordinal() + 366

    # Filter time indices that are within the date range.
    ti = np.where((dab_numeric >= st_dn) & (dab_numeric <= end_dn))[0]

    # ============================
    # Impose the super big entry fix.
    # ============================
    if ti.size > 0:
        max_t = min(ti[-1] + 1, sbub_qcdf.shape[0])
        for t in range(max(1, ti[0]), max_t):
            for i in range(ntaugp):
                if sbub_qcdf_se[t, i] > semax:
                    sbub_qcdf_se[t, i] = sbub_qcdf_se[t - 1, i]
                if sbub_qcdfp_se[t, i] > semax:
                    sbub_qcdfp_se[t, i] = sbub_qcdfp_se[t - 1, i]
                if sbub_qcdfc_se[t, i] > semax:
                    sbub_qcdfc_se[t, i] = sbub_qcdfc_se[t - 1, i]

    # --- Bubble estimates by group ---
    sbubcdf_mu      = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_se      = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_bc_mu   = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_bc_lb   = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_bc_ub   = np.zeros((nperiod, ntaugp, 3))
    bubadj_gp       = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_mu_adj  = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_bc_mu_adj = np.zeros((nperiod, ntaugp, 3))

    # --- Bubble estimates by tau group ---
    if ti.size > 0:
        for t in range(nperiod):
            tau_t = np.atleast_1d(tau[t])
            cp_t  = np.atleast_1d(cp[t])
            cp_bool = (cp_t != 0)
            ptaulist = np.unique(tau_t[np.logical_not(cp_bool)])
            ctaulist = np.unique(tau_t[cp_bool])
            taulist = np.intersect1d(ptaulist, ctaulist)
            for i in range(ntaugp):
                # Find indices in taulist within the current tau group
                gp = np.where((taulist >= taulb[i]) & (taulist <= tauub[i]))[0]
                valid_gp = gp[gp < sbub_qcdfp.shape[1]]  # Filter out invalid indices
                ngp = valid_gp.size

                if ngp > 0:
                    # Note: MATLAB third-dimension indices 1,2,3 correspond to 0,1,2 here.
                    sbubcdf_bc_mu[t, i, 0] = nzmean(sbub_qcdfp[t, valid_gp] + qcdfp_bias[t, valid_gp])
                    sbubcdf_bc_mu[t, i, 1] = nzmean(sbub_qcdfc[t, valid_gp] + qcdfc_bias[t, valid_gp])
                    sbubcdf_bc_mu[t, i, 2] = nzmean(sbub_qcdf[t, valid_gp]  + qcdf_bias[t, valid_gp])
                    sbubcdf_se[t, i, 0] = np.sqrt(nzsum(sbub_qcdfp_se[t, valid_gp]**2)) / ngp
                    sbubcdf_se[t, i, 1] = np.sqrt(nzsum(sbub_qcdfc_se[t, valid_gp]**2)) / ngp
                    sbubcdf_se[t, i, 2] = np.sqrt(nzsum(sbub_qcdf_se[t, valid_gp]**2))  / ngp
                    # Compute corrected confidence bounds.
                    sbubcdf_bc_ub[t, i, 0] = sbubcdf_bc_mu[t, i, 0] - nzmean(qcdf_Ap_lb[t, valid_gp])
                    sbubcdf_bc_ub[t, i, 1] = sbubcdf_bc_mu[t, i, 1] - nzmean(qcdf_Ac_lb[t, valid_gp])
                    sbubcdf_bc_ub[t, i, 2] = sbubcdf_bc_mu[t, i, 2] - nzmean(qcdf_A_lb[t, valid_gp])
                    sbubcdf_bc_lb[t, i, 0] = sbubcdf_bc_mu[t, i, 0] - nzmean(qcdf_Ap_ub[t, valid_gp])
                    sbubcdf_bc_lb[t, i, 1] = sbubcdf_bc_mu[t, i, 1] - nzmean(qcdf_Ac_ub[t, valid_gp])
                    sbubcdf_bc_lb[t, i, 2] = sbubcdf_bc_mu[t, i, 2] - nzmean(qcdf_A_ub[t, valid_gp])

    # --- Rolling-window averages ---
   # --- Rolling-window averages ---
    rsbubcdf_mu    = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_se    = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_bc_mu = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_bc_lb = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_bc_ub = np.zeros((nperiod, ntaugp, 3))
    
    # Handle cases where we have fewer points than bubwin0
    if len(ti) < bubwin0:
        tii = ti  # just use all points available
    else:
        tii = ti[ti >= bubwin0]
    
    mc = int(np.ceil(bubwin0 ** 0.25))
    
    if tii.size > 0:
        for t in tii:
            vt = np.arange(max(0, t - bubwin0 + 1), t + 1)
            for i in range(ntaugp):
                for j in range(3):
                    rsbubcdf_mu[t, i, j] = nzmean(sbubcdf_mu[vt, i, j])
                    rsbubcdf_se[t, i, j] = np.sqrt(
                        nzsum(sbubcdf_se[vt, i, j] ** 2) + 2 * nw_cov(sbubcdf_mu[vt, i, j], mc)
                    ) / len(vt)  # divide by actual number of points
                    rsbubcdf_bc_mu[t, i, j] = nzmean(sbubcdf_bc_mu[vt, i, j])
                    rsbubcdf_bc_lb[t, i, j] = nzmean(sbubcdf_bc_lb[vt, i, j]) - 1.96 * rsbubcdf_se[t, i, j]
                    rsbubcdf_bc_ub[t, i, j] = nzmean(sbubcdf_bc_ub[vt, i, j]) + 1.96 * rsbubcdf_se[t, i, j]



    # --- Plotting the bubble estimates ---
    esttitle = [r'$\hat\Pi_{p}(\tau)$', r'$\hat\Pi_{c}(\tau)$', r'$\hat\Pi_{cp}(\tau)$']
    legname4 = [r'$\hat\Pi(\tau),\tau\in(0.25\mp 0.1)$',
                r'$\hat\Pi(\tau),\tau\in(0.5\mp 0.15)$',
                r'$\hat\Pi(\tau),\tau\in(1\mp 0.25)$',
                f"{stockcode}"]

    # Select plotting indices: those indices in ti that are at least bubwin0.
    ttr0 = ti
    cptag = ['p', 'c', 'cp']

    # Initialize JSON data structure 
    json_data = {
        "metadata": {
            "stockcode": stockcode,
            "start_date_param": startday,
            "end_date_param": endday,
            "rolling_window_days": bubwin0,
            "num_steps": nstep,
            "optimization_threshold": opth,
            "h_number_sd": hnumsd,
            "tau_groups_info": [
                {
                    "name": "tau_1",
                    "range": f"{taulb[0]}-{tauub[0]}",
                    "mean": taumu[0]
                },
                {
                    "name": "tau_2",
                    "range": f"{taulb[1]}-{tauub[1]}",
                    "mean": taumu[1]
                },
                {
                    "name": "tau_3",
                    "range": f"{taulb[2]}-{tauub[2]}",
                    "mean": taumu[2]
                }
            ],
            "option_types_info": [
                "put",
                "call",
                "combined"
            ],
            "time_series_start_date": matlab_datenum_to_datetime(dab_numeric[ttr0[0]]).isoformat() if len(ttr0) > 0 else None,
            "time_series_end_date": matlab_datenum_to_datetime(dab_numeric[ttr0[-1]]).isoformat() if len(ttr0) > 0 else None
        },
        "time_series_data": []
    }

    # Build time series data in your requested format
    if len(ttr0) > 0:
        for idx, t in enumerate(ttr0):
            date_obj = matlab_datenum_to_datetime(dab_numeric[t])

            # Create bubble estimates for this time point
            daily_grouped = []

            # For each tau group (0, 1, 2)
            for tau_idx in range(ntaugp):
                tau_group_data = {
                    "put": {
                        "mu": float(rsbubcdf_bc_mu[t, tau_idx, 0]) if not np.isnan(rsbubcdf_bc_mu[t, tau_idx, 0]) else 0.0,
                        "lb": float(rsbubcdf_bc_lb[t, tau_idx, 0]) if not np.isnan(rsbubcdf_bc_lb[t, tau_idx, 0]) else 0.0,
                        "ub": float(rsbubcdf_bc_ub[t, tau_idx, 0]) if not np.isnan(rsbubcdf_bc_ub[t, tau_idx, 0]) else 0.0
                    },
                    "call": {
                        "mu": float(rsbubcdf_bc_mu[t, tau_idx, 1]) if not np.isnan(rsbubcdf_bc_mu[t, tau_idx, 1]) else 0.0,
                        "lb": float(rsbubcdf_bc_lb[t, tau_idx, 1]) if not np.isnan(rsbubcdf_bc_lb[t, tau_idx, 1]) else 0.0,
                        "ub": float(rsbubcdf_bc_ub[t, tau_idx, 1]) if not np.isnan(rsbubcdf_bc_ub[t, tau_idx, 1]) else 0.0
                    },
                    "combined": {
                        "mu": float(rsbubcdf_bc_mu[t, tau_idx, 2]) if not np.isnan(rsbubcdf_bc_mu[t, tau_idx, 2]) else 0.0,
                        "lb": float(rsbubcdf_bc_lb[t, tau_idx, 2]) if not np.isnan(rsbubcdf_bc_lb[t, tau_idx, 2]) else 0.0,
                        "ub": float(rsbubcdf_bc_ub[t, tau_idx, 2]) if not np.isnan(rsbubcdf_bc_ub[t, tau_idx, 2]) else 0.0
                    }
                }
                daily_grouped.append(tau_group_data)

            # Add this time point to the time series
            time_point = {
                "date": date_obj.isoformat() + "T00:00:00",
                "stock_prices": {
                    "adjusted": float(sout[t]) if not np.isnan(sout[t]) else 0.0
                },
                "bubble_estimates": {
                    "daily_grouped": daily_grouped
                }
            }

            json_data["time_series_data"].append(time_point)

    # Create the plots (same as original)
    for idx, j in enumerate(range(3), start=1):
        # Construct the bubble estimate plot for each of the three series.
        rbubplot = np.column_stack((
            rsbubcdf_bc_mu[ttr0, 0, j],
            rsbubcdf_bc_mu[ttr0, 1, j],
            rsbubcdf_bc_mu[ttr0, 2, j]
        ))
        # Adjusted price series (sout) is plotted on the right axis.
        rsplot = sout[ttr0]

        if len(ttr0) == 0:
            print(f"No data for plot index {j}, skipping this figure.")
            continue

        # Create a new figure.
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax1.set_ylabel('Bubble Estimate')

        # Plot each bubble estimate curve on the left axis.
        for col in range(rbubplot.shape[1]):
            ax1.plot(dab_numeric[ttr0], rbubplot[:, col], label=legname4[col])

        # Fill confidence intervals for each series.
        ax1.fill_between(dab_numeric[ttr0],
                         rsbubcdf_bc_lb[ttr0, 0, j],
                         rsbubcdf_bc_ub[ttr0, 0, j],
                         color='blue', alpha=0.5)
        ax1.fill_between(dab_numeric[ttr0],
                         rsbubcdf_bc_lb[ttr0, 1, j],
                         rsbubcdf_bc_ub[ttr0, 1, j],
                         color='blue', alpha=0.3)
        ax1.fill_between(dab_numeric[ttr0],
                         rsbubcdf_bc_lb[ttr0, 2, j],
                         rsbubcdf_bc_ub[ttr0, 2, j],
                         color='blue', alpha=0.2)

        ax1.set_xlim([dab_numeric[ttr0[0]], dab_numeric[ttr0[-1]]])

        # Convert MATLAB datenums to Python datetime for x-axis formatting.
        dt_dates = [matlab_datenum_to_datetime(d) for d in dab_numeric[ttr0]]
        ax1.set_xticks(dab_numeric[ttr0])
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%y'))
        ax1.xaxis_date()

        # Right axis: plot the adjusted price series.
        ax2 = ax1.twinx()
        ax2.plot(dab_numeric[ttr0], rsplot, label="Adjusted Price", color='red')
        ax2.set_ylabel("Adjusted Price")

        # Add legend and title.
        ax1.legend(loc='upper left', fontsize=12)
        ax1.set_title(esttitle[j], fontsize=12)

        fig.tight_layout()

        # Save figure as EPS and PNG
        base = f"bub{cptag[j]}_{stockcode}_splitadj_{yr1}to{yr2}"
        plt.savefig(IMG_DIR.joinpath(f"{base}.eps"), format="eps")
        plt.savefig(IMG_DIR.joinpath(f"{base}.png"), format="png")
        plt.close(fig)

    # Export JSON data with consistent naming
    json_filename = f"bubble_data_{stockcode}_splitadj_{yr1}to{yr2}.json"
    json_filepath = DATA_DIR.joinpath(json_filename)

    with open(json_filepath, 'w') as f:
        json.dump(json_data, f, indent=2, cls=NumpyEncoder)

    print(f"SUCCESS: {stockcode} - JSON saved to {json_filepath}")
    print(f"Images saved to: {IMG_DIR}")

    # Print some verification of dates
    if len(ttr0) > 0:
        first_date = matlab_datenum_to_datetime(dab_numeric[ttr0[0]])
        last_date = matlab_datenum_to_datetime(dab_numeric[ttr0[-1]])
        print(f"First date: {first_date} (MATLAB datenum: {dab_numeric[ttr0[0]]})")
        print(f"Last date: {last_date} (MATLAB datenum: {dab_numeric[ttr0[-1]]})")
        print(f"Total time series points: {len(json_data['time_series_data'])}")

    print(f"{stockcode} processing complete!")
    return True

def main():
    print(f"Processing {len(stockcodelist)} stocks...")

    # The creation of directories is moved to the global scope to avoid recreating them on each call,
    # and to ensure they exist before any stock processing starts.

    # Process each stock
    successful = []
    failed = []

    for i, stockcode in enumerate(stockcodelist, 1):
        print(f"\n[{i}/{len(stockcodelist)}] Processing {stockcode}...")

        if process_stock(stockcode):
            successful.append(stockcode)
        else:
            failed.append(stockcode)

    # Summary report
    print(f"\n{'='*60}")
    print("BATCH PROCESSING COMPLETE!")
    print(f"{'='*60}")
    print(f"Successful: {len(successful)}/{len(stockcodelist)} stocks")
    print(f"Failed: {len(failed)}/{len(stockcodelist)} stocks")

    if successful:
        print(f"\nSuccessfully processed:")
        for stock in successful:
            print(f"   - {stock}")

    if failed:
        print(f"\nFailed to process:")
        for stock in failed:
            print(f"   - {stock}")

    print(f"\nJSON files saved to: {DATA_DIR}")
    print(f"Images saved to: {IMG_DIR}")

if __name__ == '__main__':
    main()
