import numpy as np
import math
from math import factorial
from scipy.optimize import minimize
from scipy.integrate import quad

def phi(x):
    """Equivalent of MATLAB's phi(x) = exp(-x.^2/2)/sqrt(2*pi)."""
    return np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)

def d1phi(x):
    """Derivative of phi, i.e. d1phi(x) = -x * phi(x)."""
    return -x * phi(x)

def kstar(x, v, p):
    """
    Used inside 'adj'. Builds a polynomial matrix S, inverts it,
    multiplies by x^i, then multiplies by phi(x).
    """
    if pow == 0:
        S = 1
    elif pow == 1:
        S = np.array([[1, 0],
                      [0, 1]])
    elif pow == 2:
        S = np.array([[1, 0, 1],
                      [0, 1, 0],
                      [1, 0, 3]])
    elif pow == 3:
        S = np.array([[1, 0, 1, 0],
                      [0, 1, 0, 3],
                      [1, 0, 3, 0],
                      [0, 3, 0, 15]])
    else:  # pow == 4
        S = np.array([[1, 0, 1, 0, 3],
                      [0, 1, 0, 3, 0],
                      [1, 0, 3, 0, 15],
                      [0, 3, 0, 15, 0],
                      [3, 0, 15, 0, 105]])
    Sinv = np.linalg.inv(S)
    f_val = 0
    for i in range(pow+1):
        f_val += Sinv[int(v), i] * (x**i)
    return f_val * phi(x)

def adj(v, pow):
    """
    Equivalent to MATLAB's adj(v,p). Integrates kstar^2, etc.
    Returns a scaling factor used in the Fan & Yao bandwidth selection.
    """
    def kstar_sq(x):
        return kstar(x, v, pow)**2
    def kstar_poly(x):
        return (x**(pow+1)) * kstar(x, v, pow)
    def kstar_sq_zero(x):
        return kstar(x, 0, pow)**2

    i1, _ = quad(kstar_sq, -4, 4)
    i2, _ = quad(kstar_poly, -4, 4)
    i3, _ = quad(kstar_sq_zero, -4, 4)

    if pow == 0:
        Cp = 1
    elif pow == 1:
        S = np.array([[1, 0],
                      [0, 1]])
        cp = np.array([1, 0])
        Cp = 3 - (cp @ np.linalg.solve(S, cp))
    elif pow == 2:
        S = np.array([[1, 0, 1],
                      [0, 1, 0],
                      [1, 0, 3]])
        cp = np.array([0, 1, 0])
        Cp = 15 - (cp @ np.linalg.solve(S, cp))
    elif pow== 3:
        S = np.array([[1, 0, 1, 0],
                      [0, 1, 0, 3],
                      [1, 0, 3, 0],
                      [0, 3, 0, 15]])
        cp = np.array([3, 0, 1, 0])
        Cp = 105 - (cp @ np.linalg.solve(S, cp))
    else:  # pow == 4
        S = np.array([[1, 0, 1, 0, 3],
                      [0, 1, 0, 3, 0],
                      [1, 0, 3, 0, 15],
                      [0, 3, 0, 15, 0],
                      [3, 0, 15, 0, 105]])
        cp = np.array([0, 3, 0, 1, 0])
        Cp = 945 - (cp @ np.linalg.solve(S, cp))

    return ((2*v + 1)*Cp*i1) / ((pow+1 - v)*(i2**2)*i3)**(1/(2*pow+3))

def irsc(h, pk, g, pow):
    """
    Minimization target for opth=3 (Fan & Yao).
    h is log-scale in the original usage, so we do exp(h).
    """
    h_val = math.exp(h)
    nk = len(pk)
    bp = np.zeros((pow+1, nk))

    for i in range(nk):
        X = np.ones((nk,1))
        d = 0
        nu_list = []
        while d < pow:
            d += 1
            X = np.hstack([X, ((pk - pk[i])**d).reshape(-1,1)])
            nu_list.append(factorial(d))
        nu = np.array([1] + nu_list)
        W = np.diag(phi((pk - pk[i]) / h_val) / h_val)
        bp[:, i] = nu * np.linalg.solve(X.T @ W @ X, X.T @ W @ g)

    resid2 = (g - bp[0,:])**2
    resid2[np.isnan(resid2)] = 0
    resid2[np.isinf(resid2)] = 0

    rsc = np.zeros(nk)
    dk = pk[1:] - pk[:-1]
    for i in range(nk):
        X = np.ones((nk,1))
        W = np.diag(phi((pk - pk[i]) / h_val)/h_val)
        s2hat = np.linalg.solve(X.T @ W @ X, X.T @ W @ resid2)[0]
        rsc[i] = s2hat
    return np.sum(rsc[:nk-1] * dk)
# xpk[i], pk.reshape(-1,1), g, pow, ind_se, opth, hx0
def lpoly2(xpk, pk, g, pow, ind_se, opth, h0):
    """
    Local polynomial regression function (lpoly2),
    including a matrix-based variance-covariance logic for non-zero bp_se.
    Also fixes p==1 to store second derivative in bp[2].
    """
    pk = np.asarray(pk).reshape(-1)
    g  = np.asarray(g).reshape(-1)
    nk = len(pk)

    
    # Choose a constant based on p
    if pow == 1:
        hcon = 0.776
    elif pow == 2:
        hcon = 0.884
    elif pow == 3:
        hcon = 1.006
    else:
        hcon = 1.0

    alpha = None
    # Bandwidth selection
    if opth in [1, 11, 2]:
        x_mat = np.ones((nk, 1))
        d = 0
        while d < pow+3:
            d += 1
            x_mat = np.hstack([x_mat, (pk**d).reshape(-1,1)])
        alpha = np.linalg.solve(x_mat.T @ x_mat, x_mat.T @ g)
        res = g - x_mat @ alpha
        ssr = np.sum(res**2)

        w0 = lambda v: ((v > (np.mean(pk) - 1.5*np.std(pk))) & 
                        (v < (np.mean(pk) + 1.5*np.std(pk)))).astype(float)
        def mp1(v):
            return (factorial(pow+1)*alpha[pow+1] +
                    0.5*factorial(pow+2)*alpha[pow+2]*v +
                    (1/6)*factorial(pow+3)*alpha[pow+3]*v**2)

        wmp1 = np.sum(mp1(pk)**2 * w0(pk))
        if opth == 2:
            h = hcon * ((ssr * 3 * np.std(pk) / wmp1 / nk)**(1/(2*pow+3)))
        else:
            h = h0
    elif opth == 3:
        res_opt = minimize(lambda z: irsc(z, pk, g, pow), math.log(h0))
        lnh = res_opt.x[0]
        h = adj(2, pow) * math.exp(lnh)
    else:
        h = h0

    # Enforce min bandwidth if nk<10
    if nk < 10 and h < h0:
        h = h0

    # Build design matrix XX
    XX = np.ones((nk, 1))
    for d in range(1, pow+1):
        XX = np.hstack([XX, ((pk - xpk)**d).reshape(-1,1)])
        
    nu = np.array([math.factorial(d) for d in range(pow+1)])
    w_vec = phi((pk - xpk)/h) / h 

    W = np.diag(w_vec)  # diagonal matrix of weights

    # Allocate bp
    if pow == 1:
        bp = np.zeros(pow+2)  # 3 slotss
    else:
        bp = np.zeros(pow+1)



    A = XX.T @ W @ XX    # should be (p+1, p+1)
    b = XX.T @ W @ g     # should be (p+1,)
    
    temp, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)

    # Solve for local polynomial
    temp, residuals, rank, s = np.linalg.lstsq(XX.T @ W @ XX, XX.T @ W @ g, rcond=None)

    bp[:pow+1] = nu * temp  # scale each coefficient by nu[i]

    # If p==1, compute the second derivative in bp[2]
    if pow == 1:
        ker = phi((xpk - pk)/h)/h
        vx = xpk - pk
        dker = -d1phi((xpk - pk)/h)/(h**2)

        s0 = np.sum(ker)
        s1 = np.sum(vx * ker)
        s2 = np.sum(vx**2 * ker)
        t0 = np.sum(ker * g)
        t1 = np.sum(vx * ker * g)

        ds0 = np.sum(dker)
        ds1 = np.sum(vx*dker) - np.sum(ker)
        ds2 = np.sum((vx**2)*dker) - 2*np.sum(vx*ker)
        dt0 = np.sum(dker*g)
        dt1 = np.sum(vx*dker*g) - np.sum(ker*g)

        delta = s0*s2 - s1**2
        ddelta = ds0*s2 + s0*ds2 - 2*s1*ds1
        gamma = -s1*t0 + s0*t1
        dgamma = -ds1*t0 - s1*dt0 + ds0*t1 + s0*dt1

        bp[2] = (delta*dgamma - gamma*ddelta)/ (delta**2)

    # Compute squared residuals
    resid2 = (g - bp[0])**2
    resid2[np.isnan(resid2)] = 0
    resid2[np.isinf(resid2)] = 0
    resid2 = np.nan_to_num((g - bp[0])**2)   ### extra line to handle NaN/inf

    # Prepare bp_se
    if pow == 1:
        bp_se = np.zeros(pow+2)
        psize = pow+2
    else:
        bp_se = np.zeros(pow+1)
        psize = pow+1

    if ind_se == 1:
        # 1) Build S = diag(nu^2) * [ (XX'*W*XX)^(-1) * (XX'*W^2*XX) * (XX'*W*XX)^(-1) ] * diag(nu^2)
        lambda_reg = 1e-8
        invXWX = np.linalg.inv(XX.T @ W @ XX + lambda_reg * np.eye(XX.shape[1]))

        W2 = W @ W  # diagonal^2
        M = invXWX @ (XX.T @ W2 @ XX) @ invXWX
        
        # diag(nu^2) * M * diag(nu^2)
        nu_sq = np.diag(nu**2)
        S_mat = nu_sq @ M @ nu_sq

        # 2) s2hat = local variance of residuals => minimal approach
        #    s2hat = (nu * ( (XX'*W*XX)^(-1)*(XX'*W*resid2) ))[0]
        temp2 = np.linalg.pinv(XX.T @ W @ XX) @ (XX.T @ W @ resid2)

        # multiply by nu => shape pow+1
        s2hat_vec = nu * temp2
        # Typically we'd pick the first or do an average. The original code picks "resid2 - bp(1)" approach.
        # We'll do a simple average:
        s2hat = np.mean(s2hat_vec)  # or s2hat_vec[0]

        # 3) bp_var = s2hat * S_mat
        bp_var = s2hat * S_mat
        # 4) bp_se = sqrt(diag(bp_var))
        # Make sure to slice up to psize in case p=1 => length=3
        diag_vals = np.diag(bp_var)
        bp_se[:min(len(diag_vals), psize)] = np.sqrt(np.abs(diag_vals[:psize]))

    # Possibly update bandwidth if opth==1 or 11
    if alpha is not None and (opth == 1 or opth == 11):
        msr = np.mean(resid2)
        fhat = np.mean(phi((pk - xpk)/h)/h)
        lmsr = np.mean(resid2 * phi((pk - xpk)/h)/h)
        def mp1_local(v):
            return (factorial(pow+1)*alpha[pow+1] +
                    0.5*factorial(pow+2)*alpha[pow+2]*v +
                    (1/6)*factorial(pow+3)*alpha[pow+3]*v**2)
        mp1_xpk = mp1_local(xpk)
        if opth == 1:
            h = hcon*(msr/(mp1_xpk**2)/fhat/nk)**(1/(2*pow+3))
        elif opth == 11:
            h = hcon*(lmsr/(mp1_xpk**2)/fhat/nk)**(1/(2*pow+3))

    return bp, bp_se, h

# ----------------------------------------------------------------------
# Example usage to see nonzero standard errors
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import random
    random.seed(123)
    np.random.seed(123)

    nk = 12
    pk = np.linspace(0, 1, nk)
    g = np.sin(2*np.pi*pk) + 0.05*np.random.randn(nk)
    xpk = 0.5
    pow = 1         # local linear
    ind_se = 1    # compute standard errors
    opth = 1      # uses h0, then re-updates
    h0 = 0.1

    bp, bp_se, h = lpoly2(xpk, pk, g, pow, ind_se, opth, h0)
    print("bp:", bp)
    print("bp_se:", bp_se)
    print("h:", h)
