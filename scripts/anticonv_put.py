import numpy as np
import math

def anticonv_put(nint, precis, pk, put_prices, upbd):
    """
    Antitonic and convex regression.
    
    Parameters:
        nint  : int
                 Maximum number of iterations.
        prec  : float
                 Required precision for the first and second derivatives.
        x      : 1D nump     array (independent variable)
        y      : 1D numpy array (dependent variable)
        upbd   : float
                 Upper bound parameter.
                 
    Returns:
        g      : 1D numpy array
                 The antitonic and convex regression estimate.
    """
    n = len(pk)
    u = np.concatenate((np.zeros(n), np.array([1])))
    dx = pk[1:] - pk[:-1]
    dy = put_prices[1:] - put_prices[:-1]
    d2y = (put_prices[:n-2] / dx[:n-2]) - ((1/dx[:n-2] + 1/dx[1:]) * put_prices[1:n-1]) + (put_prices[2:] / dx[1:])
    k = 1
    dI = np.zeros((n+1, n+2))
    flag = 1
    a = np.zeros((n, n+1))
    
    i = 0
    while i <= n-3:
        a[i, i]   = -1/dx[i]
        a[i, i+1] = 1/dx[i] + 1/dx[i+1]
        a[i, i+2] = -1/dx[i+1]
        a[i, n]   = -d2y[i]
        i += 1

    a[n-2, 0] = 1
    a[n-2, 1] = -1
    a[n-2, n] = -dy[0]
    a[n-1, n-2] = -1
    a[n-1, n-1] = 1
    a[n-1, n]   = dy[n-2] - upbd*dx[n-2]

    while (k <= nint) and (flag == 1):
        flag = 0
        i = 0
        while i <= n-3:
            u = u - dI[:, i]
            if np.dot(a[i, :], u) > 0:
                temp = u.copy()
                scalar = np.dot(a[i, :], temp)
                denom = np.sum(a[i, :]**2)
                u = temp - scalar * a[i, :] / denom
                dI[:, i] = u - temp
            else:
                dI[:, i] = np.zeros(n+1)
            i += 1

        i = n-2
        u = u - dI[:, i]
        if np.dot(a[i, :], u) > 0:
            temp = u.copy()
            scalar = np.dot(a[i, :], temp)
            denom = np.sum(a[i, :]**2)
            u = temp - scalar * a[i, :] / denom
            dI[:, i] = u - temp
        else:
            dI[:, i] = np.zeros(n+1)

        i = n-1
        u = u - dI[:, i]
        if np.dot(a[i, :], u) > 0:
            temp = u.copy()
            scalar = np.dot(a[i, :], temp)
            denom = np.sum(a[i, :]**2)
            u = temp - scalar * a[i, :] / denom
            dI[:, i] = u - temp
        else:
            dI[:, i] = np.zeros(n+1)

        u = u - dI[:, n+1]
        temp = u.copy()
        if -u[n] > precis:
            u[n] = 0
            dI[:, n+1] = u - temp
        else:
            dI[:, n+1] = np.zeros(n+1)

        der10 = (u[0] - u[1] + u[n]*(put_prices[0]-put_prices[1]))
        der11 = (u[n-1] - u[n-2] + u[n]*(dy[n-2]-upbd*dx[n-2]))
        der2 = (- (1/dx[:n-2]) * u[:n-2] 
                + (1/dx[:n-2] + 1/dx[1:n-1]) * u[1:n-1]
                - (1/dx[1:n-1]) * u[2:n]) - u[n]*d2y

        if ( (np.sum(der10 > precis) > 0) or (np.sum(der2 > precis) > 0) or 
             (np.sum(der11 > precis) > 0) or (-u[0] > precis) ):
            flag = 1
        k += 1

    u = u / u[n]
    g = put_prices + u[:n]
    return g

# -----------------------------
# Testing the anticonv_put function
# -----------------------------
if __name__ == "__main__":
    # Create sample test data
    pk = np.linspace(1, 10, 10)    # For example, 10 points between 1 and 10
    put_prices = np.sin(pk)                 # Example function values

    nint = 1000
    precis = 1e-6
    upbd = 0.5                  # Example upper bound

    # Call the Python function
    g_python = anticonv_put(nint, precis, pk, put_prices, upbd)
    print("Regression estimate g (Python):")
    print(g_python)
    
