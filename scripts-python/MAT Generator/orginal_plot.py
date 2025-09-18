import os
import sys
import numpy as np
import scipy.io as sio
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd

# Helper functions
def datenum(date_str, fmt='%d-%b-%Y'):
    return datetime.strptime(date_str, fmt).toordinal() + 366

def matlab_datenum_to_datetime(dn):
    return datetime.fromordinal(int(dn - 366))

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

# Main Plotting Routine

def main():
    # Set up the parameters (matching the MATLAB version)
    yr1, yr2 = '1996', '2023'
    stockcode = 'SPX'

    startday = f'01JAN{yr1}'  # e.g., '01JAN1996'
    endday   = f'31DEC{yr2}'   # e.g., '31DEC2023'

    nplots = 3  # Number of bubble estimates to plot
    print('Plotting started...')

    scode, bubwin0, nstep, opth, hnumsd = stockcode, 63, 200, 0, 5
    # Build the filename using MATLAB's sprintf format, then join with the directory.
    dataname2 = os.path.join("/Users/cooperkerr/Desktop/internship/Simulation", f"optout_{scode}_{yr1}to{yr2}_splitadj_h{opth}_hsd{hnumsd}_nstep{nstep}.mat")

    print("Loading file from:", dataname2)

    # Load the MAT file with squeeze_me=True to collapse singleton dimensions.
    mat_data = sio.loadmat(dataname2, squeeze_me=True)
    #print("Keys loaded from .mat:", mat_data.keys())

    # Convert MATLAB structs to Python dictionaries.
    adjout = {name: mat_data['adjout'][name].item() if mat_data['adjout'][name].size == 1
              else mat_data['adjout'][name]
              for name in mat_data['adjout'].dtype.names}

    dataname1 = os.path.join("/Users/cooperkerr/Desktop/internship/Simulation",
                             f"optout_{scode}_{yr1}to{yr2}_h{opth}_hsd{hnumsd}_nstep{nstep}.mat")
    print("Loading file from:", dataname1)
    mat_data1 = sio.loadmat(dataname1, squeeze_me=True)

    # !!! we use the bubout and setout from the original file, not the split-adjusted one.
    bubout = {name: mat_data1['bubout'][name].item() if mat_data1['bubout'][name].size == 1
              else mat_data1['bubout'][name]
              for name in mat_data1['bubout'].dtype.names}

    setout = {name: mat_data1['setout'][name].item() if mat_data1['setout'][name].size == 1
              else mat_data1['setout'][name]
              for name in mat_data1['setout'].dtype.names}

    dataout = {name: mat_data1['dataout'][name].item() if mat_data1['dataout'][name].size == 1
               else mat_data1['dataout'][name]
                for name in mat_data1['dataout'].dtype.names}
    #print("dataout keys:", dataout.keys())

    # Explicitly load tau, cp, and dab from dataout.
    tau = dataout['tau']  # Expecting a NumPy array of 1066 elements (e.g., each element might originally be a cell array)
    cp  = dataout['cp']
    dab = dataout['da']

    # Set up tau interval parameters.
    taumu = [0.25, 0.5, 1]
    taulb = np.array([0.15, 0.35, 0.75])
    tauub = np.array([0.35, 0.65, 1.25])
    ntaugp = len(taulb)

    # Load bubble metrics from adjout.
    sbub_qcdfp     = adjout['sbub_qcdfp_adj']
    sbub_qcdfc     = adjout['sbub_qcdfc_adj']
    sbub_qcdf      = adjout['sbub_qcdf_adj']
    sbub_qcdfp_se  = adjout['sbub_qcdfp_se_adj']
    sbub_qcdfc_se  = adjout['sbub_qcdfc_se_adj']
    sbub_qcdf_se   = adjout['sbub_qcdf_se_adj']
    qcdfp_bias     = adjout['qcdfp_bias_adj']
    qcdfc_bias     = adjout['qcdfc_bias_adj']
    qcdf_bias      = adjout['qcdf_bias_adj']
    qcdf_A_lb      = adjout['qcdf_A_lb_adj']
    qcdf_A_ub      = adjout['qcdf_A_ub_adj']
    qcdf_Ap_lb     = adjout['qcdf_Ap_lb_adj']
    qcdf_Ap_ub     = adjout['qcdf_Ap_ub_adj']
    qcdf_Ac_lb     = adjout['qcdf_Ac_lb_adj']
    qcdf_Ac_ub     = adjout['qcdf_Ac_ub_adj']

    # Also from bubout:
    # does not been used. 
    scene    = bubout['scene']
    qcdfp_lb = bubout['qcdfp_lb']
    qcdfp_ub = bubout['qcdfp_ub']
    qcdfc_lb = bubout['qcdfc_lb']
    qcdfc_ub = bubout['qcdfc_ub']

    #nperiod = setout['nperiod']
    nperiod = int(setout['nperiod'])


    # Split-adjusted data.
    sout = adjout['sout_adj']

    # Set thresholds.
    qmax, semax = 1000, 1000

    # Impute "non-sensible" values for standard errors.
    sbub_qcdf_se   = np.real(sbub_qcdf_se)
    sbub_qcdfp_se  = np.real(sbub_qcdfp_se)
    sbub_qcdfc_se  = np.real(sbub_qcdfc_se)

    # Determine the number of tau columns.
    ntau = sbub_qcdf.shape[1]

    # ============================
    # Filter dates
   
    dab_numeric = np.array([int(d) - 366 for d in dab])
  

    # Convert startday and endday to Python ordinals.
    # Note: startday and endday here are strings like '01JAN1996'
    st_dn = pd.to_datetime(startday, format="%d%b%Y").toordinal()
    end_dn = pd.to_datetime(endday, format="%d%b%Y").toordinal()
    

    # Filter time indices that are within the date range.
    ti = np.where((dab_numeric >= st_dn) & (dab_numeric <= end_dn))[0]
  

    # ============================
    # Impose the super big entry fix.
    # ============================
    if ti.size > 0:
        # for t = max(2,ti(1)):ti(end)
        # In Python (0-indexed): we start from max(1, ti[0]) to ti[-1]+1 (making sure not to exceed sbub_qcdf rows)
        max_t = min(ti[-1] + 1, sbub_qcdf.shape[0])
        for t in range(max(1, ti[0]), max_t):
            for i in range(ntau):
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
        for t in range(ti[0], ti[-1] + 1):

            # Ensure tau[t] and cp[t] are treated as 1D arrays even if they are scalars.
            tau_t = np.atleast_1d(tau[t])
            cp_t  = np.atleast_1d(cp[t])

            # Convert cp_t to booleans (assuming cp values are 0/1)
            cp_bool = (cp_t != 0)

            #print("DEBUG: type(tau):", type(tau))
            #print("DEBUG: tau shape:", getattr(tau, 'shape', 'no shape'))
            #print("DEBUG: type(tau[t]):", type(tau[t]))
            #print("DEBUG: tau[t] as array shape:", tau_t.shape)
            #print("DEBUG: cp[t] as array shape:", cp_t.shape)

            ptaulist = np.unique(tau_t[np.logical_not(cp_bool)])
            # ctaulist: unique tau values where cp is True.
            ctaulist = np.unique(tau_t[cp_bool])
            # Intersection: tau values common to both groups.
            taulist = np.intersect1d(ptaulist, ctaulist)

            #print("taulist:", taulist)
            #print("ptaulist:", ptaulist)
            #print("ctaulist:", ctaulist)



            for i in range(ntaugp):
                # Find indices in taulist within the current tau group.
                gp = np.where((taulist >= taulb[i]) & (taulist <= tauub[i]))[0]
                ngp = gp.size


                #print("sbub_qcdfp shape:", sbub_qcdfp.shape)
                #print("type(sbub_qcdfp[t]):", type(sbub_qcdfp[t]))
                #print("sbub_qcdfp[t] shape (if array):", getattr(sbub_qcdfp[t], 'shape', 'not an array'))
                #print("t:", t, "gp:", gp)
                #print("max(gp):", np.max(gp) if len(gp) else None)

                if ngp > 0:
                    # Note: MATLAB third-dimension indices 1,2,3 correspond to 0,1,2 here.
                    sbubcdf_bc_mu[t, i, 0] = nzmean(sbub_qcdfp[t, gp] + qcdfp_bias[t, gp])
                    #print("DEBUG: sbub_qcdfp shape:", sbub_qcdfp.shape)
                    #print("DEBUG: type(sbub_qcdfp[t]) ->", type(sbub_qcdfp[t]))
                    #print("DEBUG: sbub_qcdfp[t] shape (if array):", getattr(sbub_qcdfp[t], 'shape', 'NOT AN ARRAY'))
                    #print("DEBUG: t:", t)
                    #print("DEBUG: gp:", gp)
                    #if len(gp) > 0:
                     #   print("DEBUG: max(gp) =", np.max(gp))

                    sbubcdf_bc_mu[t, i, 1] = nzmean(sbub_qcdfc[t, gp] + qcdfc_bias[t, gp])
                    sbubcdf_bc_mu[t, i, 2] = nzmean(sbub_qcdf[t, gp]  + qcdf_bias[t, gp])

                    sbubcdf_se[t, i, 0] = np.sqrt(nzsum(sbub_qcdfp_se[t, gp]**2)) / ngp
                    sbubcdf_se[t, i, 1] = np.sqrt(nzsum(sbub_qcdfc_se[t, gp]**2)) / ngp
                    sbubcdf_se[t, i, 2] = np.sqrt(nzsum(sbub_qcdf_se[t, gp]**2))  / ngp

                    # Compute corrected confidence bounds.
                    sbubcdf_bc_ub[t, i, 0] = sbubcdf_bc_mu[t, i, 0] - nzmean(qcdf_Ap_lb[t, gp])
                    sbubcdf_bc_ub[t, i, 1] = sbubcdf_bc_mu[t, i, 1] - nzmean(qcdf_Ac_lb[t, gp])
                    sbubcdf_bc_ub[t, i, 2] = sbubcdf_bc_mu[t, i, 2] - nzmean(qcdf_A_lb[t, gp])

                    sbubcdf_bc_lb[t, i, 0] = sbubcdf_bc_mu[t, i, 0] - nzmean(qcdf_Ap_ub[t, gp])
                    sbubcdf_bc_lb[t, i, 1] = sbubcdf_bc_mu[t, i, 1] - nzmean(qcdf_Ac_ub[t, gp])
                    sbubcdf_bc_lb[t, i, 2] = sbubcdf_bc_mu[t, i, 2] - nzmean(qcdf_A_ub[t, gp])

    # --- Rolling-window averages ---
    rsbubcdf_mu    = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_se    = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_bc_mu = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_bc_lb = np.zeros((nperiod, ntaugp, 3))
    rsbubcdf_bc_ub = np.zeros((nperiod, ntaugp, 3))

    tii = ti[ti >= bubwin0]  # Ensure rolling window has sufficient data

    mc = int(np.ceil(bubwin0 ** 0.25))


    if tii.size > 0:
        for t in range(tii[0], tii[-1] + 1):
            vt = np.arange(t - bubwin0 + 1, t + 1)
            for i in range(ntaugp):
                for j in range(3):
                    rsbubcdf_mu[t, i, j] = nzmean(sbubcdf_mu[vt, i, j])
                    rsbubcdf_se[t, i, j] = np.sqrt(
                        nzsum(sbubcdf_se[vt, i, j] ** 2) + 2 * nw_cov(sbubcdf_mu[vt, i, j], mc)
                    ) / bubwin0
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
    ttr0 = ti[ti >= bubwin0]
    cptag = ['p', 'c', 'cp']

    for idx, j in enumerate(range(3), start=1):
        # Construct the bubble estimate plot for each of the three series.
        # In MATLAB, columns 1,2,3 of rsbubcdf_bc_mu are used.
        rbubplot = np.column_stack((
            rsbubcdf_bc_mu[ttr0, 0, j],
            rsbubcdf_bc_mu[ttr0, 1, j],
            rsbubcdf_bc_mu[ttr0, 2, j]
        ))
        # Adjusted price series (sout) is plotted on the right axis.
        rsplot = sout[ttr0]

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


        



        if len(ttr0) == 0:
            print(f"No data for plot index {j}, skipping this figure.")
            continue


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
        # Save figure as EPS.
        from pathlib import Path

        # Folder where you want every figure to go
        IMG_DIR = Path(__file__).resolve().parent.parent / "images"
        IMG_DIR.mkdir(exist_ok=True)          # create it if it doesn't exist

        base = f"bub{cptag[j]}_{stockcode}_h{opth}_hsd{hnumsd}_{yr1}to{yr2}"

        plt.savefig(IMG_DIR / f"{base}.eps", format="eps")
        plt.savefig(IMG_DIR / f"{base}.png", format="png")
        plt.close(fig)



"""
        save_filename = f"bub{cptag[j]}_{stockcode}_h{opth}_hsd{hnumsd}_{yr1}to{yr2}.eps"
        plt.savefig(save_filename, format='eps')
        png_name = save_filename.replace('.eps', '.png')
        plt.savefig(png_name, format='png')
        plt.close(fig)
        
        for pct in range(1, 101):
            sys.stdout.write(f"\rPlot {idx}/{nplots}: {pct}%")
            sys.stdout.flush()
"""
        #print("\nPlotting complete for bubble estimate:", esttitle[j])


if __name__ == '__main__':
    main()
