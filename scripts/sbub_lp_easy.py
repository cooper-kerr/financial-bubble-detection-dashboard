import warnings
import numpy as np
import pandas as pd
from anticonv_put import anticonv_put
from anticonv_call import anticonv_call
from lpoly2 import lpoly2
from nw_cov import nw_cov
from datetime import datetime

def sbub_lp_easy(data_file, count_file, yr1, yr2, pow, nstep, opth, hnumsd):
    # --- settings &  warnings off ---
    warnings.filterwarnings("ignore", message="Python:nearlySingularMatrix")
    warnings.filterwarnings("ignore", message="Python:SingularMatrix")
    minrange, maxcdfjump = 0.3, 0.7
    nint, precis = 500, 1e-5

    ind_se = 0
    modelname = 'cls6secp'
    np.random.seed(1234)

# ========= Importing Count Data =========
    count_file = '/Users/cooperkerr/Desktop/internship/Simulation/optout_^SPX_count.csv'
    # ========= Importing Count Data =========
    if not os.path.exists(count_file):
        raise FileNotFoundError(f"Count file not found: {count_file}")
    df_count = pd.read_csv(count_file)
    nkcnt = df_count.iloc[:,1].astype(int).values
    nperiod = len(nkcnt)
    print(f"Found {nperiod} dates from count file.")
    print(f"Found {nperiod} dates from count file: {os.path.basename(count_file)}")

    # ------------- Read the main data file ------------

    data_file = '/Users/cooperkerr/Desktop/internship/Simulation/optout_^SPX.csv'
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")
    df = pd.read_csv(data_file)
    total = df.shape[0]
    if total != nkcnt.sum():
        raise ValueError(f"sum(nkcnt)={nkcnt.sum()} but found {total} rows in data file")

    

    # Initialize dictionaries (equivalent to MATLAB cell arrays)
    dateraw = {}
    cp_flag = {}
    exdateraw = {}
    tauday = {}
    X = {}
    s = {}
    tr = {}
    money = {}
    oprice = {}
    volume = {}
    iv = {}
    deltachk = {}
    cp = {}
    ncall = {}
    tau = {}
    sout = {}
    da = {}

    # Set nperiod as the number of rows in the CSV (nlines)
    start = 0
    for t in range(nperiod):
        nt = nkcnt[t]
        block = df.iloc[start:start+nt]
        start += nt


        dateraw[t]   = block.iloc[:,0].astype(str).tolist()
        cp_flag[t]   = block.iloc[:,1].astype(str).tolist()
        exdateraw[t] = block.iloc[:,2].astype(str).tolist()
        tauday[t]    = block.iloc[:,3].astype(float).tolist()
        X[t]         = block.iloc[:,4].astype(float).tolist()
        s[t]         = block.iloc[:,5].astype(float).tolist()
        tr[t]        = block.iloc[:,6].astype(float).tolist()
        money[t]     = block.iloc[:,7].astype(float).tolist()
        oprice[t]    = block.iloc[:,8].astype(float).tolist()
        volume[t]    = block.iloc[:,9].astype(float).tolist()
        iv[t]        = block.iloc[:,10].astype(float).tolist()
        deltachk[t]  = block.iloc[:,11].astype(float).tolist()


        # cp: assign 1 if cp_flag equals 'C', else 0.
        cp[t] = [1 if f=='C' else 0 for f in cp_flag[t]]
        ncall[t] = sum(cp[t])

        # tau{t} = tauday{t}/365
        tau[t] = [d/365.0 for d in tauday[t]]

        # sout(t) = s{t}(1)
        sout[t] = s[t][0]

        # da(t,1)=datenum(dateraw{t}(1),'ddmmmyyyy')
        da[t] = datetime.strptime(dateraw[t][0], '%d%b%Y').toordinal() +366





    # ========= Calibration =========
    max_groups = max(
        len(np.intersect1d(
            np.unique(np.array(tau[t])[np.array(cp[t],bool)==0]),
            np.unique(np.array(tau[t])[np.array(cp[t],bool)==1])
        ))
        for t in range(nperiod)
    )
    #print("maximum tau‐groups in any period:", max_groups)
    mntau = max_groups

    # Create arrays for calibration (dimensions: nperiod x mntau)
    nkc = np.zeros((nperiod, mntau))
    nkp = np.zeros((nperiod, mntau))
    sumvolc = np.zeros((nperiod, mntau))
    sumvolp = np.zeros((nperiod, mntau))

    otmc = np.zeros((nperiod, mntau))
    call1_arr = np.zeros((nperiod, mntau))
    sbub_qcdfp = np.zeros((nperiod, mntau))
    sbub_qcdfc = np.zeros((nperiod, mntau))
    sbub_qcdf  = np.zeros((nperiod, mntau))

    sbub_qcdfp_se = np.zeros((nperiod, mntau))
    sbub_qcdfc_se = np.zeros((nperiod, mntau))
    sbub_qcdf_se  = np.zeros((nperiod, mntau))

    qcdfp_bias = np.zeros((nperiod, mntau))
    qcdfc_bias = np.zeros((nperiod, mntau))
    qcdf_bias  = np.zeros((nperiod, mntau))
    qcdf_A_lb  = np.zeros((nperiod, mntau))
    qcdf_A_ub  = np.zeros((nperiod, mntau))
    qcdf_Ap_lb = np.zeros((nperiod, mntau))
    qcdf_Ap_ub = np.zeros((nperiod, mntau))
    qcdf_Ac_lb = np.zeros((nperiod, mntau))
    qcdf_Ac_ub = np.zeros((nperiod, mntau))
    qcdf_B1    = np.zeros((nperiod, mntau))
    qcdf_B21   = np.zeros((nperiod, mntau))
    qcdf_B22   = np.zeros((nperiod, mntau))
    qcdf_B23   = np.zeros((nperiod, mntau))
    qcdf_B3    = np.zeros((nperiod, mntau))

    Bcbub_lb = np.zeros((nperiod, mntau))
    Bcbub_ub = np.zeros((nperiod, mntau))

    scene = np.zeros((nperiod, mntau))
    qcdfp_lb = np.zeros((nperiod, mntau))
    qcdfp_ub = np.zeros((nperiod, mntau))
    qcdfc_lb = np.zeros((nperiod, mntau))
    qcdfc_ub = np.zeros((nperiod, mntau))
    lp = np.zeros((nperiod, mntau))
    up = np.zeros((nperiod, mntau))
    lc = np.zeros((nperiod, mntau))
    uc = np.zeros((nperiod, mntau))



    # For storing optimal bandwidths, etc.
    hxopt = {}

    # Loop over each period t ( t = 0, ..., nperiod-1)
    for t in range(nperiod):

        #print(f"\n\n=== Period {t+1}/{nperiod} (date ordinal {da[t]}) ===")

        pb = np.floor(10 * (t+1) / (nperiod+1))
        if t > 0 and pb > np.floor(10 * t / (nperiod+1)):
            print(f"{int(pb):2d} ", end='')

        # Extract tau and cp for period t (as numpy arrays)
        tau_t = np.array(tau[t])
        cp_t  = np.array(cp[t], dtype=bool)

        # Determine unique tau values for puts and calls respectively:
        ptaulist = np.unique(tau_t[~cp_t])
        ctaulist = np.unique(tau_t[cp_t])
        taulist_common = np.intersect1d(ptaulist, ctaulist)

        ntau_t = len(taulist_common)

        for j in range(ntau_t):
            #print(f"  -- tau group {j+1}/{len(taulist_common)}: τ={taulist_common[j]:.4f}")
            # For the j-th tau group in period t:
            vput = (tau_t == taulist_common[j]) & (~cp_t)
            np_val = np.sum(vput)
            put_prices = np.array(oprice[t])[vput]

            pk = np.array(X[t])[vput]
            if np_val > 1:
                dk = np.diff(pk)
            else:
                dk = np.array([0])
            volp = np.array(volume[t])[vput]

            vcall = (tau_t == taulist_common[j]) & (cp_t)
            nc_val = np.sum(vcall)
            call_prices = np.array(oprice[t])[vcall]

            ck = np.array(X[t])[vcall]   #define ck as all accesss

            if nc_val > 1:

                dck = np.diff(ck)
            else:
                dck = np.array([0])
            volc = np.array(volume[t])[vcall]

            # Create strike grid for puts
            pstep = (pk[-1] - pk[0]) / nstep if nstep != 0 else 0
            xpk = np.linspace(pk[0], pk[-1], num=nstep+1)
            nxp = len(xpk)

            # CLS parameters
            upbd = np.exp(-np.array(tr[t])[0] * taulist_common[j])

            # Compute puts’ “density” and force it into an N×1 column vector
            #print("    puts:", np_val, "strikes pk.shape=", pk.shape, "prices shape=", put_prices.shape)
            g = anticonv_put(
        +       nint, precis,
        +       pk.flatten(),
        +       put_prices.flatten(),
        +       upbd)
            #print("    → g.shape=", g.shape)


            # Now proceed with the local‐polynomial grid for puts
            qcdfp = np.zeros(nxp)
            qcdfp_se_pt = np.zeros(nxp)
            hx0 = np.mean(dk) * hnumsd if np.any(dk) else 0

            for i in range(nxp):
                bg, bg_se, hpopt0 = lpoly2(
                    xpk[i],
                    pk.reshape(-1, 1),
                    g,
                    pow, ind_se, opth, hx0
                )
                if opth in (1, 11):
                    bg, bg_se = lpoly2(
                        xpk[i],
                        pk.reshape(-1, 1),
                        g,
                        pow, ind_se, 0, hpopt0
                    )
                qcdfp_out = bg[1] / upbd
                qcdfp_se_pt[i] = bg_se[1] / upbd
                qcdfp[i] = np.clip(qcdfp_out, 0, 1)
                hxopt.setdefault((t, j), []).append(hpopt0)

            # Adjust qcdfp for flat portions
            for i in range(1, nxp):
                if qcdfp[i-1] == 1:
                    qcdfp[i] = 1
            for i in range(nxp-1, 0, -1):
                if qcdfp[i] == 0:
                    qcdfp[i-1] = 0
            for i in range(nxp):
                if qcdfp[i] == 0 or qcdfp[i] == 1 or qcdfp_se_pt[i] > 1:
                    qcdfp_se_pt[i] = 0

            qcdfp_range = np.max(qcdfp) - np.min(qcdfp)
            dqcdfp = np.diff(qcdfp)
            if qcdfp_range > minrange and np.max(dqcdfp) < maxcdfjump:
                qcdfp_norm = (qcdfp - np.min(qcdfp)) / qcdfp_range
                qcdfp_mu = (np.nansum(1 - qcdfp_norm) * pstep + xpk[0]) * upbd
                mp = int(np.ceil(nxp**0.25))
                wp = np.ones(nxp) * pstep * upbd / qcdfp_range
                wp[0] = (upbd * pstep * np.sum(qcdfp) - (put_prices[-1] - put_prices[0])) / (qcdfp_range**2) + upbd * pstep / qcdfp_range
                wp[-1] = -(upbd * pstep * np.sum(qcdfp) - (put_prices[-1] - put_prices[0])) / (qcdfp_range**2) + upbd * pstep / qcdfp_range
                qcdfp_pt = qcdfp * wp
                qcdfp_norm_se_pt = qcdfp_se_pt * wp
                # guard against tiny negative variance from nw_cov
                var_term = np.nansum(qcdfp_norm_se_pt**2) + 2 * nw_cov(qcdfp_pt, mp)
                if var_term < 0:
                    var_term = 0.0
                qcdfp_se = np.sqrt(var_term)
            else:
                qcdfp_mu = sout[t]
                qcdfp_se = 0
                np_val = 0

            # === Process Calls (analogous to puts) ===

            gc = anticonv_call(
        +        nint, precis,
        +        ck.flatten(),
        +        call_prices.flatten(),
        +        upbd)

            cstep = (ck[-1] - ck[0]) / nstep if nstep != 0 else 0
            xck = np.linspace(ck[0], ck[-1], num=nstep+1)
            nxc = len(xck)  
            qcdfc = np.zeros(nxc)
            qcdfc_se_pt = np.zeros(nxc)
            hx0 = np.mean(dck) * hnumsd if np.any(dck) else 0

            for i in range(nxc):
                bgc, bgc_se, hcopt0 = lpoly2(xck[i], ck.reshape(-1,1), gc, pow, ind_se, opth, hx0)
                if opth == 1 or opth == 11:
                    bgc, bgc_se = lpoly2(xck[i], ck.reshape(-1,1), gc, pow, ind_se, 0, hcopt0)

                qcdfc_out = 1 + bgc[1] / upbd
                qcdfc_se_pt[i] = bgc_se[1] / upbd
                qcdfc[i] = np.clip(qcdfc_out, 0, 1)
                hxopt.setdefault((t, j, 'call'), []).append(hcopt0)

            for i in range(1, nxc):
                if qcdfc[i-1] == 1:
                    qcdfc[i] = 1
            for i in range(nxc-1, 0, -1):
                if qcdfc[i] == 0:
                    qcdfc[i-1]  = 0
                    print(f"[t={t}, j={j}] qcdfc before zeroing: {qcdfc}")
                    print(f"[t={t}, j={j}] qcdfc_se_pt before zeroing: {qcdfc_se_pt}")
                    if np.any(qcdfc_se_pt != 0):
                        print("[t={}, j={}] NONZERO qcdfc_se_pt detected: {}".format(t, j, qcdfc_se_pt))

            for i in range(nxc):
                if qcdfc[i] == 0 or qcdfc[i] == 1 or qcdfc_se_pt[i] > 1:
                    qcdfc_se_pt[i] = 0
                    print(f"[t={t}, j={j}] qcdfc_se_pt after zeroing: {qcdfc_se_pt}")


            qcdfc_range = np.max(qcdfc) - np.min(qcdfc)
            dqcdfc = np.diff(qcdfc)
            print(f"  → tau‐group {j}: qcdfc_range={qcdfc_range:.4f}, max(dqcdfc)={np.nanmax(dqcdfc):.4f} "
            f"(thresholds minrange={minrange}, maxcdfjump={maxcdfjump})")

            if qcdfc_range > minrange and np.max(dqcdfc) < maxcdfjump:
                qcdfc_norm = (qcdfc - np.min(qcdfc)) / qcdfc_range
                qcdfc_mu = (np.nansum(1 - qcdfc_norm) * cstep + xck[0]) * upbd
                mc = int(np.ceil(nxc**0.25))
                wc = np.ones(nxc) * cstep * upbd / qcdfc_range
                wc[0] = (upbd * cstep * np.sum(qcdfc) - (call_prices[-1] - call_prices[0] + upbd*(ck[-1]-ck[0]))) / (qcdfc_range**2) + upbd * cstep / qcdfc_range
                wc[-1] = -(upbd * cstep * np.sum(qcdfc) - (call_prices[-1] - call_prices[0] + upbd*(ck[-1]-ck[0]))) / (qcdfc_range**2) + upbd * cstep / qcdfc_range
                qcdfc_pt = qcdfc * wc
                qcdfc_norm_se_pt = qcdfc_se_pt * wc
                qcdfc_norm_se_pt_squared_sum = np.nansum(qcdfc_norm_se_pt**2)
                nw_cov_result = nw_cov(qcdfc_pt, mc)
                total_variance = qcdfc_norm_se_pt_squared_sum + 2 * nw_cov_result

                print("qcdfc_norm_se_pt_squared_sum:", qcdfc_norm_se_pt_squared_sum)
                print("nw_cov_result:", nw_cov_result)
                print("total_variance (value inside sqrt):", total_variance)
                # Safety check to avoid NaNs
                if total_variance < 0:
                    total_variance = 0.0   # clamp tiny negatives
                qcdfc_se = np.sqrt(total_variance)
                print(f"[t={t}, j={j}] qcdfc_se (just calculated) = {qcdfc_se}")


            else:
                qcdfc_mu = sout[t]
                qcdfc_se = 0
                nc_val = 0

            # Combine strike grids of calls and puts
            xk = np.union1d(xpk, xck)
            n = nc_val + np_val
            if n > 0:
                qcdf_mu = (np_val/n)*qcdfp_mu + (nc_val/n)*qcdfc_mu
                qcdf_se = np.sqrt(((np_val/n)*qcdfp_se)**2 + ((nc_val/n)*qcdfc_se)**2)
            else:
                qcdf_mu = sout[t]
                qcdf_se = 0

            # Bias computations: find indices with conditions

            lc_p_arr = np.where(pk >= ck[0])[0]
            lc_p = lc_p_arr[0] if lc_p_arr.size > 0 else np.where(pk <= ck[0])[0][-1]
            up_c_arr = np.where(ck <= pk[-1])[0]
            up_c = up_c_arr[-1] if up_c_arr.size > 0 else np.where(ck >= pk[-1])[0][0]
            lp_c_arr = np.where(ck >= pk[0])[0]
            lp_c = lp_c_arr[0] if lp_c_arr.size > 0 else np.where(ck <= pk[0])[0][-1]
            uc_p_arr = np.where(pk <= ck[-1])[0]
            uc_p = uc_p_arr[-1] if uc_p_arr.size > 0 else np.where(pk >= ck[-1])[0][0]

            if qcdfp_range > minrange:
                B1p = upbd * np.min(qcdfp) * (pk[-1] - pk[0]) / qcdfp_range
                B2p = (1/qcdfp_range - 1) * (put_prices[-1] - put_prices[0])
            else:
                B1p = 0
                B2p = 0
            if qcdfc_range > minrange:
                B1c = upbd * np.min(qcdfc) * (ck[-1] - ck[0]) / qcdfc_range
                B2c = (1/qcdfc_range - 1) * (upbd*(ck[-1]-ck[0]) + call_prices[-1] - call_prices[0])
            else:
                B1c = 0
                B2c = 0

            A_lb = -put_prices[0] if np_val > 0 else 0
            A_ub = call_prices[-1] if nc_val > 0 else 0
            Ap_lb = -put_prices[0] if np_val > 0 else 0
            Ap_ub = call_prices[up_c] if nc_val > 0 else 0
            Ac_lb = -put_prices[lc_p] if np_val > 0 else 0
            Ac_ub = call_prices[-1] if nc_val > 0 else 0

            if n > 0:
                B1 = (np_val * B1p + nc_val * B1c) / n
                B21 = (np_val * B2p + nc_val * B2c) / n
                B3 = np_val/n * upbd*(ck[-1]-pk[-1])
                if pk[0] <= ck[0] and pk[-1] <= ck[-1] and ck[0] <= pk[-1]:
                    B22 = np_val/n*(upbd*(ck[-1]-pk[-1]) + call_prices[-1] - call_prices[up_c])
                    B23 = nc_val/n*(put_prices[lc_p]-put_prices[0])
                    scene[t, j] = 1
                elif ck[0] <= pk[0] and ck[-1] <= pk[-1] and pk[0] <= ck[-1]:
                    B22 = -np_val/n*(put_prices[-1]-put_prices[uc_p])
                    B23 = -nc_val/n*(upbd*(pk[0]-ck[0]) + call_prices[lp_c]-call_prices[0])
                    scene[t, j] = 2
                elif pk[0] <= ck[0] and ck[-1] <= pk[-1]:
                    B22 = nc_val/n*(put_prices[lc_p]-put_prices[0])
                    B23 = -np_val/n*(put_prices[-1]-put_prices[uc_p])
                    scene[t, j] = 3
                elif ck[0] <= pk[0] and pk[-1] <= ck[-1]:
                    B22 = -nc_val/n*(upbd*(pk[0]-ck[0]) + call_prices[lp_c]-call_prices[0])
                    B23 = np_val/n*(upbd*(ck[-1]-pk[-1]) + call_prices[-1]-call_prices[up_c])
                    scene[t, j] = 4
                elif pk[-1] < ck[0]:
                    B22 = nc_val/n*(put_prices[-1]-put_prices[0])
                    B23 = np_val/n*(upbd*(ck[-1]-ck[0]) + call_prices[-1]-call_prices[0])
                    A_ub = call_prices[-1] + upbd
                    scene[t, j] = 5
                else:
                    B22 = 0
                    B23 = 0
                    scene[t, j] = 6

            else:
                B1 = 0
                B21 = 0
                B22 = 0
                B23 = 0
                B3 = 0

            qcdfp_bias[t, j] = B1p - B2p
            qcdfc_bias[t, j] = B1c - B2c
            qcdf_bias[t, j] = B1 - B21 + B22 + B23 - B3
            qcdf_A_lb[t, j] = A_lb
            qcdf_A_ub[t, j] = A_ub
            qcdf_Ap_lb[t, j] = Ap_lb
            qcdf_Ap_ub[t, j] = Ap_ub
            qcdf_Ac_lb[t, j] = Ac_lb
            qcdf_Ac_ub[t, j] = Ac_ub
            qcdf_B1[t, j] = B1
            qcdf_B21[t, j] = B21
            qcdf_B22[t, j] = B22
            qcdf_B23[t, j] = B23
            qcdf_B3[t, j] = B3


            # compute bub

            otmc[t, j] = call_prices[-1]
            call1_arr[t, j] = call_prices[0]

            sbub_qcdfp[t, j] = sout[t] - qcdfp_mu
            sbub_qcdfc[t, j] = sout[t] - qcdfc_mu
            sbub_qcdf[t, j] = sout[t] - qcdf_mu

            sbub_qcdfp_se[t, j] = qcdfp_se
            sbub_qcdfc_se[t, j] = qcdfc_se
            print(f"[t={t}, j={j}] sbub_qcdfc_se[t, j] (assigned) = {sbub_qcdfc_se[t, j]}")
            sbub_qcdf_se[t, j] = qcdf_se

            qcdfp_lb[t, j] = np.min(qcdfp)
            qcdfp_ub[t, j] = np.max(qcdfp)
            qcdfc_lb[t, j] = np.min(qcdfc)
            qcdfc_ub[t, j] = np.max(qcdfc)

            lp[t, j] = pk[0]
            up[t, j] = pk[-1]
            lc[t, j] = ck[0]
            uc[t, j] = ck[-1]

            nkp[t, j] = np_val
            nkc[t, j] = nc_val

            sumvolc[t, j] = np.sum(volc)
            sumvolp[t, j] = np.sum(volp)

            qcdfc_range = np.max(qcdfc) - np.min(qcdfc)
            if qcdfc_range > 0:
                factor = -(1.0 / qcdfc_range - 1.0)
                Bcbub_lb[t, j] = factor * call_prices[0]
                Bcbub_ub[t, j] = factor * call_prices[-1]
            else:
                Bcbub_lb[t, j] = 0.0
                Bcbub_ub[t, j] = 0.0
    # end for t
    # end calibration

    # --- Report ---
    bubout = {}
    bubout['otmc'] = otmc
    bubout['call1'] = call1_arr
    bubout['sbub_qcdfp'] = sbub_qcdfp
    bubout['sbub_qcdfc'] = sbub_qcdfc
    bubout['sbub_qcdf'] = sbub_qcdf
    bubout['sbub_qcdfp_se'] = sbub_qcdfp_se
    bubout['sbub_qcdfc_se'] = sbub_qcdfc_se
    bubout['sbub_qcdf_se'] = sbub_qcdf_se

    bubout['qcdfp_bias'] = qcdfp_bias
    bubout['qcdfc_bias'] = qcdfc_bias
    bubout['qcdf_bias'] = qcdf_bias
    bubout['qcdf_A_lb'] = qcdf_A_lb
    bubout['qcdf_A_ub'] = qcdf_A_ub
    bubout['qcdf_Ap_lb'] = qcdf_Ap_lb
    bubout['qcdf_Ap_ub'] = qcdf_Ap_ub
    bubout['qcdf_Ac_lb'] = qcdf_Ac_lb
    bubout['qcdf_Ac_ub'] = qcdf_Ac_ub
    bubout['qcdf_B1'] = qcdf_B1
    bubout['qcdf_B21'] = qcdf_B21
    bubout['qcdf_B22'] = qcdf_B22
    bubout['qcdf_B23'] = qcdf_B23
    bubout['qcdf_B3'] = qcdf_B3

    bubout['Bcbub_lb'] = Bcbub_lb
    bubout['Bcbub_ub'] = Bcbub_ub

    bubout['scene'] = scene
    bubout['qcdfp_lb'] = qcdfp_lb
    bubout['qcdfp_ub'] = qcdfp_ub
    bubout['qcdfc_lb'] = qcdfc_lb
    bubout['qcdfc_ub'] = qcdfc_ub
    bubout['lp'] = lp
    bubout['up'] = up
    bubout['lc'] = lc
    bubout['uc'] = uc
    2
    bubout['nkc'] = nkc
    bubout['nkp'] = nkp
    bubout['sumvolc'] = sumvolc
    bubout['sumvolp'] = sumvolp

    setout = {}
    setout['filesource'] = filesource
    setout['modelname'] = modelname
    setout['yr1'] = yr1
    setout['yr2'] = yr2
    setout['pow'] = pow
    setout['nstep'] = nstep
    setout['opth'] = opth
    setout['hnumsd'] = hnumsd
    setout['nperiod'] = nperiod

    dataout = {}
    dataout['sout'] = sout
    dataout['oprice'] = oprice
    dataout['cp'] = cp
    dataout['X'] = X
    dataout['tau'] = tau
    dataout['tr'] = tr
    dataout['da'] = da
    print("sbub_qcdfc_se array at end:", sbub_qcdfc_se)


    return bubout, dataout, setout

