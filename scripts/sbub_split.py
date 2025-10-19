
import numpy as np
from scipy.io import loadmat
from datetime import datetime
import scipy.io as sio

def datenum(date_str, fmt='%d-%b-%Y'):
    """Convert a date string (e.g. '21-Jun-2000') to a MATLAB datenum equivalent."""
    return datetime.strptime(date_str, fmt).toordinal() + 366

def sbub_split(stockcode, dataname, yr1, yr2):
    # Initialize splitratio and define splitdate/splitratio based on the stockcode
    splitratio = []
    splitdate = []
    
    if stockcode == 'AAPL':
        splitdate = ['21-Jun-2000', '28-Feb-2005', '9-Jun-2014', '31-Aug-2020']
        splitratio = [2, 2, 7, 4]
    elif stockcode == 'GOOG':
        splitdate = ['3-Apr-2014']
        splitratio = [1.998]
    elif stockcode == 'TSLA':
        splitdate = ['31-Aug-2020']
        splitratio = [5]
    elif stockcode == 'AMZN':
        splitdate = ['2-Jun-1998', '5-Jan-1999', '2-Sep-1999']
        splitratio = [2, 3, 2]
    elif stockcode == 'MSFT':
        splitdate = ['9-Dec-1996', '23-Feb-1998', '29-Mar-1999', '18-Feb-2003']
        splitratio = [2, 2, 2, 2]
    elif stockcode == 'INTC':
        splitdate = ['14-Jul-1997', '12-Apr-1999', '31-Jul-2000']
        splitratio = [2, 2, 2]
    elif stockcode == 'T':
        splitdate = ['20-Mar-1998', '18-Nov-2002']
        splitratio = [2, 24875/50000]
    elif stockcode == 'NVDA':
        splitdate = ['27-Jun-2000', '17-Sep-2001', '7-Apr-2006', '11-Sep-2007', '20-Jul-2021']
        splitratio = [2, 2, 2, 1.5, 4]
    elif stockcode == 'AIG':
        splitdate = ['28-Jul-1997', '3-Aug-1998', '2-Aug-1999', '31-Jul-2000', '1-Jul-2009']
        splitratio = [1.5, 1.5, 5/4, 1.5, 1/20]
    elif stockcode == 'AMD':
        splitdate = ['22-Aug-2000']
        splitratio = [2]
    elif stockcode == 'PG':
        splitdate = ['22-Sep-1997', '21-Jun-2004']
        splitratio = [2, 2]
    elif stockcode == 'BAC':
        splitdate = ['28-Feb-1997', '30-Aug-2004']
        splitratio = [2, 2]
    elif stockcode == 'JNJ':
        splitdate = ['12-Jun-1996', '13-Jun-2001']
        splitratio = [2, 2]
    elif stockcode == 'NFLX':
        splitdate = ['12-Feb-2004', '15-Jul-2015']
        splitratio = [2, 7]
    elif stockcode == 'GE':
        splitdate = ['12-May-1997', '8-May-2000', '26-Feb-2019', '2-Aug-2021']
        splitratio = [2, 3, 1.04, 1/8]
    elif stockcode == 'TEVA':
        splitdate = ['23-Feb-2000', '6-Dec-2002', '1-Jul-2004']
        splitratio = [2, 2, 2]
    elif stockcode == 'MU':
        splitdate = ['2-May-2000']
        splitratio = [2]
    elif stockcode == 'TWTR':
        splitdate = ['3-Dec-1999']
        splitratio = [2]
    elif stockcode == 'WFC':
        splitdate = ['14-Oct-1997', '14-Aug-2006']
        splitratio = [2, 2]
    elif stockcode == 'CSCO':
        splitdate = ['20-Feb-1996', '17-Dec-1997', '16-Sep-1998', '22-Jun-1999', '23-Mar-2000']
        splitratio = [2, 1.5, 1.5, 2, 2]
    elif stockcode == 'PBR':
        splitdate = ['2-Jul-2007', '8-May-2008']
        splitratio = [2, 2]
    elif stockcode == 'MPC':
        splitdate = ['11-Jun-2015']
        splitratio = [2]
    elif stockcode == 'XOM':
        splitdate = ['14-Apr-1997', '19-Jul-2001']
        splitratio = [2, 2]
    elif stockcode == 'BA':
        splitdate = ['9-Jun-1997']
        splitratio = [2]
    elif stockcode == 'FCX':
        splitdate = ['2-Feb-2011']
        splitratio = [2]
    elif stockcode == 'F':
        splitdate = ['8-Apr-1998', '29-Jun-2000', '3-Aug-2000']
        splitratio = [10000/6641, 10000/9607, 1.748175]
    elif stockcode == 'BIDU':
        splitdate = ['12-May-2010']
        splitratio = [10]
    elif stockcode == 'AMRN':
        splitdate = ['19-Oct-1998']
        splitratio = [0.1]
    elif stockcode == 'MS':
        splitdate = ['15-Jan-1997', '27-Jan-2000']
        splitratio = [2, 2]
    elif stockcode == 'BMY':
        splitdate = ['3-Mar-1997', '1-Mar-1999', '7-Aug-2001']
        splitratio = [2, 2, 1000000/951777]
    elif stockcode == 'PFE':
        splitdate = ['1-Jul-1997', '1-Jul-1999', '17-Nov-2020']
        splitratio = [2, 3, 1.054]
    elif stockcode == 'SBUX':
        splitdate = ['22-Mar-1999', '30-Apr-2001', '24-Oct-2005', '9-Apr-2015']
        splitratio = [2, 2, 2, 2]
    elif stockcode == 'WMT':
        splitdate = ['20-Apr-1999']
        splitratio = [2]
    elif stockcode == 'QCOM':
        splitdate = ['11-May-1999', '31-Dec-1999', '16-Aug-2004']
        splitratio = [2, 4, 2]
    elif stockcode == 'UNH':
        splitdate = ['26-Dec-2000', '19-Jun-2003', '31-May-2005']
        splitratio = [2, 2, 2]
    elif stockcode == 'V':
        splitdate = ['19-Mar-2015']
        splitratio = [4]
    elif stockcode == 'MA':
        splitdate = ['22-Jan-2014']
        splitratio = [10]
    elif stockcode == 'LLY':
        splitdate = ['16-Oct-1997']
        splitratio = [2]
    elif stockcode == 'CVX':
        splitdate = ['13-Sep-2004']
        splitratio = [2]
    elif stockcode == 'KO':
        splitdate = ['13-May-1996', '13-Aug-2012']
        splitratio = [2, 2]
    elif stockcode == 'COST':
        splitdate = ['14-Jan-2000']
        splitratio = [2]
    elif stockcode == 'TMO':
        splitdate = ['6-Jun-1996']
        splitratio = [1.5]
    elif stockcode == 'MRK':
        splitdate = ['17-Feb-1999']
        splitratio = [2]
    elif stockcode == 'DHR':
        splitdate = ['1-Jun-1998', '21-May-2004', '14-Jun-2010', '5-Jul-2016']
        splitratio = [2, 2, 2, 1.319]
    elif stockcode == 'ORCL':
        splitdate = ['17-Apr-1996', '18-Aug-1997', '1-Mar-1999', '19-Jan-2000', '13-Oct-2000']
        splitratio = [1.5, 1.5, 1.5, 2, 2]
    elif stockcode == 'ADBE':
        splitdate = ['27-Oct-1999', '25-Oct-2000', '24-May-2005']
        splitratio = [2, 2, 2]
    elif stockcode == 'MCD':
        splitdate = ['8-Mar-1999']
        splitratio = [2]
    elif stockcode == 'ABT':
        splitdate = ['1-Jun-1998', '3-May-2004', '2-Jan-2013']
        splitratio = [2, 10000/9356, 10000/4798]
    elif stockcode == 'C':
        splitdate = ['28-May-1996', '25-Nov-1996', '20-Nov-1997', '1-Jun-1999', '28-Aug-2000', '9-May-2011']
        splitratio = [1.5, 4/3, 1.5, 1.5, 4/3, 0.1]
    elif stockcode == 'EEM':
        splitdate = ['9-Jun-2005', '24-Jul-2008']
        splitratio = [3, 3]
    elif stockcode == 'QQQ':
        splitdate = ['20-Mar-2000']
        splitratio = [2]
    elif stockcode == 'FXI':
        splitdate = ['24-Jul-2008']
        splitratio = [3]
    elif stockcode == 'IWM':
        splitdate = ['9-Jun-2005']
        splitratio = [2]
    elif stockcode == 'XOP':
        splitdate = ['30-Mar-2020']
        splitratio = [0.25]
    elif stockcode == 'XLF':
        splitdate = ['19-Sep-2016']
        splitratio = [1.231]
    elif stockcode == 'SLV':
        splitdate = ['24-Jul-2008']
        splitratio = [10]
    elif stockcode == 'EFA':
        splitdate = ['9-Jun-2005']
        splitratio = [3]
    elif stockcode == 'GME':
        splitdate = ['19-Mar-2007']
        splitratio = [2]
    else:
        splitdate = []
        splitratio = []
    
    nsplit = len(splitratio)
    
    # Create start and end date strings using the provided years
    stdate = "1-Jan-" + str(yr1)
    endate = "31-Dec-" + str(yr2)
    
    # Assume the file was saved as dataname+".npz" containing variables dataout and bubout.
    mat_filename = dataname
    mat_data = loadmat(mat_filename, squeeze_me=True)

    # Extract structured arrays from .mat file
    dataout = mat_data["dataout"]
    
    bubout = mat_data["bubout"]

    if isinstance(dataout, np.ndarray) and dataout.dtype == 'O':
        dataout = dataout.item()

    if isinstance(bubout, np.ndarray) and bubout.dtype == 'O':
        bubout = bubout.item()
    
    

# Access fields if dataout and bubout are structured arrays
# For example, if you need field "sout" from dataout:
# sout = dataout["sout"].item()

    
    # Extract variables from the loaded structures
    da = dataout['da'].item()

    sout_adj = dataout['sout'].item()
    otmc_adj = bubout['otmc'].item()
    sbub_qcdfp_adj = bubout['sbub_qcdfp'].item()
    sbub_qcdfc_adj = bubout['sbub_qcdfc'].item()
    sbub_qcdf_adj = bubout['sbub_qcdf'].item()
    qcdfp_bias_adj = bubout['qcdfp_bias'].item()
    qcdfc_bias_adj = bubout['qcdfc_bias'].item()
    qcdf_bias_adj = bubout['qcdf_bias'].item()
    sbub_qcdfp_se_adj = bubout['sbub_qcdfp_se'].item()
    sbub_qcdfc_se_adj = bubout['sbub_qcdfc_se'].item()
    sbub_qcdf_se_adj = bubout['sbub_qcdf_se'].item()
    qcdf_A_lb_adj = bubout['qcdf_A_lb'].item()
    qcdf_A_ub_adj = bubout['qcdf_A_ub'].item()
    qcdf_Ap_lb_adj = bubout['qcdf_Ap_lb'].item()
    qcdf_Ap_ub_adj = bubout['qcdf_Ap_ub'].item()
    qcdf_Ac_lb_adj = bubout['qcdf_Ac_lb'].item()
    qcdf_Ac_ub_adj = bubout['qcdf_Ac_ub'].item()

    
    # Adjust values based on split events within the specified date range
    if nsplit > 0:
        for i in range(nsplit):
            current_split = datenum(splitdate[i])
            if current_split > datenum(stdate) and current_split < datenum(endate):
                vt = da < current_split  # Boolean mask for dates before the split
                
                sout_adj[vt] = sout_adj[vt] / splitratio[i]
                otmc_adj[vt, :] = otmc_adj[vt, :] / splitratio[i]
                sbub_qcdfp_adj[vt, :] = sbub_qcdfp_adj[vt, :] / splitratio[i]
                sbub_qcdfc_adj[vt, :] = sbub_qcdfc_adj[vt, :] / splitratio[i]
                sbub_qcdf_adj[vt, :] = sbub_qcdf_adj[vt, :] / splitratio[i]
                qcdfp_bias_adj[vt, :] = qcdfp_bias_adj[vt, :] / splitratio[i]
                qcdfc_bias_adj[vt, :] = qcdfc_bias_adj[vt, :] / splitratio[i]
                qcdf_bias_adj[vt, :] = qcdf_bias_adj[vt, :] / splitratio[i]
                sbub_qcdfp_se_adj[vt, :] = sbub_qcdfp_se_adj[vt, :] / splitratio[i]
                sbub_qcdfc_se_adj[vt, :] = sbub_qcdfc_se_adj[vt, :] / splitratio[i]
                sbub_qcdf_se_adj[vt, :] = sbub_qcdf_se_adj[vt, :] / splitratio[i]
                
                qcdf_A_lb_adj[vt, :] = qcdf_A_lb_adj[vt, :] / splitratio[i]
                qcdf_A_ub_adj[vt, :] = qcdf_A_ub_adj[vt, :] / splitratio[i]
                qcdf_Ap_lb_adj[vt, :] = qcdf_Ap_lb_adj[vt, :] / splitratio[i]
                qcdf_Ap_ub_adj[vt, :] = qcdf_Ap_ub_adj[vt, :] / splitratio[i]
                qcdf_Ac_lb_adj[vt, :] = qcdf_Ac_lb_adj[vt, :] / splitratio[i]
                qcdf_Ac_ub_adj[vt, :] = qcdf_Ac_ub_adj[vt, :] / splitratio[i]
    
    # Create the output structure as a dictionary
    adjout = {}
    adjout["sout_adj"] = sout_adj
    adjout["otmc_adj"] = otmc_adj

    adjout["sbub_qcdfp_adj"] = sbub_qcdfp_adj
    adjout["sbub_qcdfc_adj"] = sbub_qcdfc_adj
    adjout["sbub_qcdf_adj"] = sbub_qcdf_adj
    adjout["qcdfp_bias_adj"] = qcdfp_bias_adj
    adjout["qcdfc_bias_adj"] = qcdfc_bias_adj
    adjout["qcdf_bias_adj"] = qcdf_bias_adj
    adjout["sbub_qcdfp_se_adj"] = sbub_qcdfp_se_adj
    adjout["sbub_qcdfc_se_adj"] = sbub_qcdfc_se_adj
    adjout["sbub_qcdf_se_adj"] = sbub_qcdf_se_adj
    adjout["qcdf_A_lb_adj"] = qcdf_A_lb_adj
    adjout["qcdf_A_ub_adj"] = qcdf_A_ub_adj
    adjout["qcdf_Ap_lb_adj"] = qcdf_Ap_lb_adj
    adjout["qcdf_Ap_ub_adj"] = qcdf_Ap_ub_adj
    adjout["qcdf_Ac_lb_adj"] = qcdf_Ac_lb_adj
    adjout["qcdf_Ac_ub_adj"] = qcdf_Ac_ub_adj

    result = (adjout, dataout, bubout)
    print("→ sbub_split is about to return:", result)
    print("   length:", len(result))
    
    return adjout, dataout, bubout





