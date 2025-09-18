"""
Reading the csv files and converting them into a pandas dataframe
to underatand the data better.

"""
from anticonv_put import anticonv_put
from lpoly2 import lpoly2
from nw_cov import nw_cov
import numpy as np
import pandas as pd

# Load data clearly

class Dataloader:
    
       

    def get_main_data(self):
        return pd.read_csv('/Users/cooperkerr/Desktop/internship/Simulation/optout_SPX_1996to2023.csv')
    
    def get_count_data(self):
        return pd.read_csv('/Users/cooperkerr/Desktop/internship/Simulation/optout_SPX_1996to2023_count.csv')

   


data_info = Dataloader()
df_main = data_info.get_main_data()[:10]
df_put = data_info.get_main_data()
df_count = data_info.get_count_data()
print(df_put.head())
    
print(df_count.head())



df_put = pd.read_csv('/Users/cooperkerr/Desktop/internship/Simulation/optout_SPX_1996to2023.csv')

# Parameters clearly
nint = 1000
precis = 1e-6
pow = 2
ind_se = 1
opth = 0
hx0 = 0.5

# Extract unique dates or tau clearly for creating a series
unique_dates = df_put['date'].unique()

# Initialize list to store estimates clearly (series)
intercept_series = []

for current_date in unique_dates:
    # Filter data for current date clearly
    df_current = df_put[df_put['date'] == current_date]

    pk = df_current['strike'].values
    put_prices = df_current['callprice'].values
    tau = df_current['tau'].iloc[0]
    tr = df_current['tr'].iloc[0]

    # Compute upbd (upper bound) clearly
    upbd = np.exp(-tr * tau / 365)

    # Run anticonvex regression clearly
    g_val = anticonv_put(nint, precis, pk, put_prices, upbd)

    # Run local polynomial regression clearly at mean strike
    x0_strike = np.mean(pk)  # choosing a representative strike clearly
    bg, bg_se, hpopt0 = lpoly2(x0_strike, pk, g_val, pow, ind_se, opth, hx0)

    # Store the primary coefficient (e.g., intercept) clearly
    intercept_series.append(bg[0])

# Convert clearly to numpy array
intercept_series = np.array(intercept_series)

# Now clearly integrate with nw_cov
lags = int(np.ceil(len(intercept_series)**0.25))
cov_est = nw_cov(intercept_series, lags)
robust_se = np.sqrt(cov_est)

print("Robust standard error (NW covariance) clearly calculated:", robust_se)






