import os
import numpy as np
from scipy.io import savemat
from .sbub_lp_easy import sbub_lp_easy
from .sbub_split import sbub_split

def run_mat_generator(stockcode, yr1, yr2, input_dir, output_dir):
    """
    Runs the MAT file generation process for a single stock.
    """
    print(f"--- Starting MAT Generator for {stockcode} ---")

    # Fixed parameters
    pow, nstep, opth, hnumsd = 2, 200, 0, 5

    os.makedirs(output_dir, exist_ok=True)

    # Build filenames
    filesource = f"optout_{stockcode}"
    count_file = os.path.join(input_dir, f"{filesource}_{yr1}to{yr2}_count.csv")
    data_file  = os.path.join(input_dir, f"{filesource}_{yr1}to{yr2}.csv")
    
    dataname = f"optout_{stockcode}_{yr1}to{yr2}_h{opth}_hsd{hnumsd}_nstep{nstep}"
    matfile = os.path.join(output_dir, dataname + ".mat")
    
    dataname2 = f"optout_{stockcode}_{yr1}to{yr2}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}"
    splitfile = os.path.join(output_dir, dataname2 + ".mat")

    # Bubble estimation
    if os.path.exists(matfile):
        print(f"{matfile} already exists — skipping bubble estimation.")
    else:
        if not os.path.exists(count_file) or not os.path.exists(data_file):
            print(f"Input CSV files not found for {stockcode}. Skipping bubble estimation.")
            return

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
        setout_struct['yr1'] = yr1
        setout_struct['yr2'] = yr2


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

        savemat(matfile, mat_dict)
        print(f"Saved results to {matfile}")

    # Split adjustment
    if os.path.exists(splitfile):
        print(f"{splitfile} already exists — skipping split adjustment.")
    else:
        if not os.path.exists(matfile):
            print(f"Input MAT file not found for {stockcode}. Skipping split adjustment.")
            return
            
        adjout, _, _ = sbub_split(stockcode, matfile, yr1, yr2)
        adjout_clean = {key: (value if value is not None else np.array([])) for key, value in adjout.items()}
        savemat(splitfile, {'adjout': adjout_clean})
        print(f"Saved split-adjusted results to {splitfile}")
        
    print(f"--- Finished MAT Generator for {stockcode} ---")
scripts-python/mat_to_json.py

This is the detailed JSON generator, refactored as a function and with the plotting logic removed.

import os
import numpy as np
import scipy.io as sio
from datetime import datetime, date
import json

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

def matlab_datenum_to_datetime(matlab_datenum):
    return date.fromordinal(int(matlab_datenum) - 366)

def nw_cov(q, m):
    mu = np.mean(q)
    n = len(q)
    gam = np.zeros(m)
    cov_val = 0.0
    for j in range(1, m + 1):
        gam[j - 1] = np.sum((q[:n - j] - mu) * (q[j:] - mu)) / n
        cov_val += (1 - j / (m + 1)) * gam[j - 1]
    return cov_val
    
def mat_to_json(stockcode, yr1, yr2, input_dir, output_dir):
    """Process a single stock and generate detailed JSON"""
    print(f"\n--- Starting MAT to JSON conversion for {stockcode}... ---")

    startday = f'01JAN{yr1}'
    endday   = f'31DEC{yr2}'
    bubwin0, nstep, opth, hnumsd = 63, 200, 0, 5

    dataname_base = f"optout_{stockcode}_{yr1}to{yr2}_h{opth}_hsd{hnumsd}_nstep{nstep}"
    reference_file_path = os.path.join(input_dir, f"{dataname_base}.mat")
    dataname2_path = os.path.join(input_dir, f"optout_{stockcode}_{yr1}to{yr2}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}.mat")

    try:
        mat_data = sio.loadmat(dataname2_path, squeeze_me=True)
        adjout = {name: mat_data['adjout'][name].item() if mat_data['adjout'][name].size == 1 else mat_data['adjout'][name] for name in mat_data['adjout'].dtype.names}

        mat_data1 = sio.loadmat(reference_file_path, squeeze_me=True)
        bubout = {name: mat_data1['bubout'][name].item() if mat_data1['bubout'][name].size == 1 else mat_data1['bubout'][name] for name in mat_data1['bubout'].dtype.names}
        setout = {name: mat_data1['setout'][name].item() if mat_data1['setout'][name].size == 1 else mat_data1['setout'][name] for name in mat_data1['setout'].dtype.names}
        dataout = {name: mat_data1['dataout'][name].item() if mat_data1['dataout'][name].size == 1 else mat_data1['dataout'][name] for name in mat_data1['dataout'].dtype.names}
    except FileNotFoundError as e:
        print(f"ERROR: One or more .mat files not found for {stockcode}: {e}")
        return False
    except Exception as e:
        print(f"An error occurred while loading .mat files for {stockcode}: {e}")
        return False

    tau = dataout['tau']
    cp  = dataout['cp']
    dab = dataout['da']

    taumu = [0.25, 0.5, 1]
    taulb = np.array([0.15, 0.35, 0.75])
    tauub = np.array([0.35, 0.65, 1.25])
    ntaugp = len(taulb)

    sbub_qcdfp = adjout['sbub_qcdfp_adj']
    sbub_qcdfc = adjout['sbub_qcdfc_adj']
    sbub_qcdf = adjout['sbub_qcdf_adj']
    sbub_qcdfp_se = adjout['sbub_qcdfp_se_adj']
    sbub_qcdfc_se = adjout['sbub_qcdfc_se_adj']
    sbub_qcdf_se = adjout['sbub_qcdf_se_adj']
    qcdfp_bias = adjout['qcdfp_bias_adj']
    qcdfc_bias = adjout['qcdfc_bias_adj']
    qcdf_bias = adjout['qcdf_bias_adj']
    qcdf_A_lb = adjout['qcdf_A_lb_adj']
    qcdf_A_ub = adjout['qcdf_A_ub_adj']
    qcdf_Ap_lb = adjout['qcdf_Ap_lb_adj']
    qcdf_Ap_ub = adjout['qcdf_Ap_ub_adj']
    qcdf_Ac_lb = adjout['qcdf_Ac_lb_adj']
    qcdf_Ac_ub = adjout['qcdf_Ac_ub_adj']

    nperiod = int(setout['nperiod'])
    sout = adjout['sout_adj']
    semax = 1000

    sbub_qcdf_se = np.real(sbub_qcdf_se)
    sbub_qcdfp_se = np.real(sbub_qcdfp_se)
    sbub_qcdfc_se = np.real(sbub_qcdfc_se)

    ntau = sbub_qcdf.shape[1]
    
    dab_numeric = np.array([int(d) for d in dab])
    st_dn = datetime.strptime(startday, "%d%b%Y").toordinal() + 366
    end_dn = datetime.strptime(endday, "%d%b%Y").toordinal() + 366
    ti = np.where((dab_numeric >= st_dn) & (dab_numeric <= end_dn))[0]
    
    if ti.size > 0:
        max_t = min(ti[-1] + 1, sbub_qcdf.shape[0])
        for t in range(max(1, ti[0]), max_t):
            for i in range(ntaugp):
                if sbub_qcdf_se[t, i] > semax: sbub_qcdf_se[t, i] = sbub_qcdf_se[t - 1, i]
                if sbub_qcdfp_se[t, i] > semax: sbub_qcdfp_se[t, i] = sbub_qcdfp_se[t - 1, i]
                if sbub_qcdfc_se[t, i] > semax: sbub_qcdfc_se[t, i] = sbub_qcdfc_se[t - 1, i]

    sbubcdf_bc_mu = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_se = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_bc_ub = np.zeros((nperiod, ntaugp, 3))
    sbubcdf_bc_lb = np.zeros((nperiod, ntaugp, 3))

    if ti.size > 0:
        for t in range(nperiod):
            tau_t = np.atleast_1d(tau[t])
            cp_t  = np.atleast_1d(cp[t])
            cp_bool = (cp_t != 0)
            ptaulist = np.unique(tau_t[~cp_bool])
            ctaulist = np.unique(tau_t[cp_bool])
            taulist = np.intersect1d(ptaulist, ctaulist)
            for i in range(ntaugp):
                gp = np.where((taulist >= taulb[i]) & (taulist <= tauub[i]))[0]
                valid_gp = gp[gp < sbub_qcdfp.shape[1]]
                ngp = valid_gp.size
                if ngp > 0:
                    sbubcdf_bc_mu[t, i, 0] = np.nanmean(sbub_qcdfp[t, valid_gp] + qcdfp_bias[t, valid_gp])
                    sbubcdf_bc_mu[t, i, 1] = np.nanmean(sbub_qcdfc[t, valid_gp] + qcdfc_bias[t, valid_gp])
                    sbubcdf_bc_mu[t, i, 2] = np.nanmean(sbub_qcdf[t, valid_gp]  + qcdf_bias[t, valid_gp])
                    sbubcdf_se[t, i, 0] = np.sqrt(np.nansum(sbub_qcdfp_se[t, valid_gp]**2)) / ngp
                    sbubcdf_se[t, i, 1] = np.sqrt(np.nansum(sbub_qcdfc_se[t, valid_gp]**2)) / ngp
                    sbubcdf_se[t, i, 2] = np.sqrt(np.nansum(sbub_qcdf_se[t, valid_gp]**2))  / ngp
                    sbubcdf_bc_ub[t, i, 0] = sbubcdf_bc_mu[t, i, 0] - np.nanmean(qcdf_Ap_lb[t, valid_gp])
                    sbubcdf_bc_ub[t, i, 1] = sbubcdf_bc_mu[t, i, 1] - np.nanmean(qcdf_Ac_lb[t, valid_gp])
                    sbubcdf_bc_ub[t, i, 2] = sbubcdf_bc_mu[t, i, 2] - np.nanmean(qcdf_A_lb[t, valid_gp])
                    sbubcdf_bc_lb[t, i, 0] = sbubcdf_bc_mu[t, i, 0] - np.nanmean(qcdf_Ap_ub[t, valid_gp])
                    sbubcdf_bc_lb[t, i, 1] = sbubcdf_bc_mu[t, i, 1] - np.nanmean(qcdf_Ac_ub[t, valid_gp])
                    sbubcdf_bc_lb[t, i, 2] = sbubcdf_bc_mu[t, i, 2] - np.nanmean(qcdf_A_ub[t, valid_gp])

    rsbubcdf_bc_mu = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_bc_lb = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_bc_ub = np.zeros((nperiod, ntaugp, 3))
    
    ttr0 = ti[ti >= bubwin0]

    json_data = {
        "metadata": {
            "stockcode": stockcode,
            "start_date_param": startday,
            "end_date_param": endday
        },
        "time_series_data": []
    }

    if len(ttr0) > 0:
        for t in ttr0:
            date_obj = matlab_datenum_to_datetime(dab_numeric[t])
            daily_grouped = []
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
            time_point = {
                "date": date_obj.isoformat() + "T00:00:00",
                "stock_prices": {"adjusted": float(sout[t]) if not np.isnan(sout[t]) else 0.0},
                "bubble_estimates": {"daily_grouped": daily_grouped}
            }
            json_data["time_series_data"].append(time_point)

    os.makedirs(output_dir, exist_ok=True)
    json_filename = f"bubble_data_{stockcode}_splitadj_{yr1}to{yr2}.json"
    json_filepath = os.path.join(output_dir, json_filename)

    with open(json_filepath, 'w') as f:
        json.dump(json_data, f, indent=2, cls=NumpyEncoder)

    print(f"SUCCESS: {stockcode} - JSON saved to {json_filepath}")
    return True
