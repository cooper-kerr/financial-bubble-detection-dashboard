import numpy as np

#nint, precis, ck.reshape(-1,1), np.array(call_prices).reshape(-1,1), upbd
def anticonv_call(nint, precis, ck, call_prices, upbd):
    """

    Parameters:
        nint : int
            Maximum number of iterations.
        precis : float
            Required precision for the first and second derivatives.
        x     : 1D numpy array (independent variable)
        y     : 1D numpy array (dependent variable)
        upbd  : float
            Upper bound parameter.
    
    Returns:
        g     : 1D numpy array
            The antitonic and convex regression estimate.
    
    Notes:
        - In MATLAB, dy(n-1) is the last element of dy. In Python, the last
          element of dy_vals (length n-1) is dy_vals[n-2].
        - If n < 3, the second-derivative constraints may not make sense,
          so use caution with very small datasets.
    """

    n = len(ck)
   
    u = np.concatenate((np.zeros(n), np.array([1])))

    # First differences
    dx = ck[1:] - ck[:-1]         # length n-1
    dy_vals = call_prices[1:] - call_prices[:-1]    # length n-1

# Second differences
    d2y = (
        (call_prices[:n-2] / dx[:n-2])
        - ((1/dx[:n-2] + 1/dx[1:]) * call_prices[1:n-1])
        + (call_prices[2:] / dx[1:])
    )

    k = 1
    flag = 1

    # dI is (n+1) x (n+2)
    dI = np.zeros((n+1, n+2))
    # a is n x (n+1)
    a = np.zeros((n, n+1))

    
    i = 0
    while i <= n-3:
        a[i, i]   = -1 / dx[i]
        a[i, i+1] = 1 / dx[i] + 1 / dx[i+1]
        a[i, i+2] = -1 / dx[i+1]
        a[i, n]   = -d2y[i]
        i += 1
    #
    # With 0-based indexing and the fix:
    a[n-2, n-1] = 1
    a[n-2, n-2] = -1
    # Instead of dy_vals[n-1], we use dy_vals[n-2] (the last difference)
    if n-2 < len(dy_vals):
        a[n-2, n] = dy_vals[n-2]
    else:
        # If for some reason n-2 >= len(dy_vals), fallback or set 0
        a[n-2, n] = 0

    # Last row of a
    a[n-1, 0] = 1
    a[n-1, 1] = -1
    # Here we do not change dy_vals[0]
    a[n-1, n] = -dy_vals[0] - upbd * dx[0]

    # Iterative projection loop
    while (k <= nint) and (flag == 1):
        flag = 0

        # For i=1 to n-2 => i=0..n-3 in Python
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

        # i = n-2
        i = n - 2
        u = u - dI[:, i]
        if np.dot(a[i, :], u) > 0:
            temp = u.copy()
            scalar = np.dot(a[i, :], temp)
            denom = np.sum(a[i, :]**2)
            u = temp - scalar * a[i, :] / denom
            dI[:, i] = u - temp
        else:
            dI[:, i] = np.zeros(n+1)

        # i = n-1
        i = n - 1
        u = u - dI[:, i]
        if np.dot(a[i, :], u) > 0:
            temp = u.copy()
            scalar = np.dot(a[i, :], temp)
            denom = np.sum(a[i, :]**2)
            u = temp - scalar * a[i, :] / denom
            dI[:, i] = u - temp
        else:
            dI[:, i] = np.zeros(n+1)

        # The (n+1)-th column => Python index n+1
        u = u - dI[:, n+1]
        temp = u.copy()
        if -u[n] > precis:
            u[n] = 0
            dI[:, n+1] = u - temp
        else:
            dI[:, n+1] = np.zeros(n+1)

        # Convergence checks
        #  use dy_vals[n-2] for the last difference
        der10 = (u[n-1] - u[n-2])
        if n-2 < len(dy_vals):
            der10 += u[n] * dy_vals[n-2]

        #uses dy(1) => the *first* difference => dy_vals[0] 
        der11 = (-u[1] + u[0]) + u[n] * (-dy_vals[0] - upbd * dx[0])

        der2 = (
            - (1 / dx[:n-2]) * u[:n-2]
            + (1 / dx[:n-2] + 1 / dx[1:n-1]) * u[1:n-1]
            - (1 / dx[1:n-1]) * u[2:n]
        ) - u[n] * d2y

        if (
            (np.sum(der10 > precis) > 0)
            or (np.sum(der2 > precis) > 0)
            or (np.sum(der11 > precis) > 0)
            or (-u[0] > precis)
        ):
            flag = 1
        k += 1

    # Normalize u
    u = u / u[n]
    # Final regression estimate
    g = call_prices + u[:n]
    return g


#its just for testing purposes
# -----------------------------
# Example usage:
if __name__ == "__main__":
    # Example with n=9 points (the original cause of the IndexError)
    import numpy as np

    ck = np.linspace(1, 9, 9)   # n=9
    call_prices = np.cos(ck)
    nint = 1000
    precis = 1e-6
    upbd = 0.5

    g_est = anticonv_call(nint, precis, ck, call_prices, upbd)
    print("Regression estimate g (anticonv_call) with n=9 points:")
    print(g_est)

    # Example: after running g_est = anticonv_call(...)

    # 1) Check antitonic
    diff_g = np.diff(g_est)
    is_antitonic = np.all(diff_g <= 0)
    print("First differences of g:", diff_g)
    print("Is g non-increasing (antitonic)?", is_antitonic)

    # 2) Check convexity
    diff2_g = np.diff(diff_g)
    is_convex = np.all(diff2_g >= 0)
    print("Second differences of g:", diff2_g)
    print("Is g convex?", is_convex)
