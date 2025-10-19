


import numpy as np

def nw_cov(q, m):
    """
    Newey-West covariance estimator.
    
    Parameters:
        q : 1D numpy array
            The input data series.
        m : int
            The number of lags to use.
            
    Returns:
        cov_val : float
            The Newey-West covariance estimate.
    
    This function computes:
      mu = mean(q)
      For j=1:m:
          gam(j) = sum((q(1:n-j)-mu).*(q(1+j:n)-mu))/n
      cov = sum_{j=1}^{m} (1 - j/(m+1))*gam(j)
    """
    mu = np.mean(q)
    n = len(q)
    gam = np.zeros(m)
    cov_val = 0.0
    for j in range(1, m+1):
        # q[0:n-j] corresponds to MATLAB q(1:n-j)
        # q[j:n] corresponds to MATLAB q(1+j:n)
        gam[j-1] = np.sum((q[:n-j] - mu) * (q[j:] - mu)) / n
        cov_val += (1 - j/(m+1)) * gam[j-1]
    return cov_val
