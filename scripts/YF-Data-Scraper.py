import os
from pathlib import Path
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred
from scipy.stats import norm

csv_dir = "data/csv"

# Automatically detect tickers from CSV filenames, ignore _count files
tickers = [
    f.replace("optout_", "").replace(".csv", "")
    for f in os.listdir(csv_dir)
    if f.startswith("optout_") and not f.endswith("_count.csv")
]

# FRED API key from environment variable
api_key = os.getenv("FRED_API_KEY")
if not api_key:
    raise ValueError("FRED_API_KEY environment variable not set")
fred = Fred(api_key=api_key)

for ticker_symbol in tickers:
    
    print(f"Running scraper for {ticker_symbol}...")

    filesource = f"optout_{ticker_symbol}"  # for CSV filenames
    save_folder = csv_dir
    os.makedirs(save_folder, exist_ok=True)

    start_date = "1996-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    ticker = yf.Ticker(ticker_symbol)
    
    start_date = "1996-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    historical_data = ticker.history(start=start_date, end=end_date)
    closing_prices = historical_data[['Close']].reset_index()
    closing_prices.rename(columns={'Date': 'date', 'Close': 'snp'}, inplace=True)
    closing_prices['date'] = pd.to_datetime(closing_prices['date']).dt.tz_localize(None)
    indexdata_processed = closing_prices
    #--------------------Treasury Data
    series_id = "DGS1MO"
    data = fred.get_series(series_id, start_date, end_date)
    
    df = pd.DataFrame(data, columns=["tr"])
    df.index.name = 'date'
    df = df.reset_index()
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)  # tz-naive
    df['tr'] = df['tr']/100
    #--------------Options Data------------
    
    ticker = yf.Ticker(ticker_symbol)
    expirations = ticker.options
    today = datetime.now()
    
    # include options expiring within the next 365 days
    expirations_this_year = [
        date for date in expirations
        if today <= datetime.strptime(date, '%Y-%m-%d') <= today + timedelta(days=365)
    ]
    
    all_options = pd.DataFrame()
    for expiration_date in expirations_this_year:
        try:
            options = ticker.option_chain(expiration_date)
            
            calls = options.calls.copy()
            calls['exdate'] = pd.to_datetime(expiration_date)
            calls['cp_flag'] = 'C'
            
            puts = options.puts.copy()
            puts['exdate'] = pd.to_datetime(expiration_date)
            puts['cp_flag'] = 'P'
            
            all_options = pd.concat([all_options, calls, puts], ignore_index=True)
            print(f"Fetched options data for expiration date: {expiration_date}")
        except Exception as e:
            print(f"Error fetching options data for {expiration_date}: {e}")
    
    all_options = all_options.rename(columns={'lastTradeDate': 'date'})
    all_options = all_options[['date', 'exdate', 'cp_flag', 'strike', 'bid', 'ask',
                               'volume', 'openInterest', 'impliedVolatility']]
    
    all_options['callprice'] = (all_options['bid'] + all_options['ask']) / 2
    all_options['date'] = all_options['date'].dt.date
    cols_to_convert = ['strike', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
    all_options[cols_to_convert] = all_options[cols_to_convert].apply(pd.to_numeric, errors='coerce')
    all_options['strike'] = all_options['strike']/1000
    all_options = all_options[all_options['volume'] > 0]
    # 2. Best bid or offer at least $0.05
    all_options = all_options[(all_options['bid'] >= 0.05) | (all_options['ask'] >= 0.05)]
    all_options['date'] = pd.to_datetime(all_options['date']).dt.tz_localize(None)
    all_options['exdate'] = pd.to_datetime(all_options['exdate']).dt.tz_localize(None)
    # 3. Time-to-maturity > 8 days and <= 1 year
    all_options['tau'] = (all_options['exdate'] - all_options['date']).dt.days
    all_options = all_options[(all_options['tau'] > 8) & (all_options['tau'] <= 365)]
    # all_options already has tau in days
    # Optional: create tau in years for grouping
    all_options['tau_years'] = all_options['tau'] / 365  # 252 trading days ≈ 1 year
    
    # Define maturity groups using tau_years
    def classify_maturity_group(tau_years):
        if tau_years <= 0.25:
            return '0-3M'
        elif tau_years <= 0.5:
            return '3-6M'
        else:
            return '6-12M'
    
    all_options['maturity_group'] = all_options['tau_years'].apply(classify_maturity_group)
    
    # Filter out groups with fewer than 3 observations per date, cp_flag, maturity_group
    group_counts = all_options.groupby(['date', 'cp_flag', 'maturity_group']).size().reset_index(name='n_obs')
    valid_groups = group_counts[group_counts['n_obs'] >= 3]
    
    # Keep only valid groups
    all_options = all_options.merge(
        valid_groups[['date', 'cp_flag', 'maturity_group']], 
        on=['date', 'cp_flag', 'maturity_group'], 
        how='inner'
    )
    strike_counts = all_options.groupby(['date', 'cp_flag', 'tau'])['strike'].nunique().reset_index(name='n_strikes')
    valid_strikes = strike_counts[strike_counts['n_strikes'] >= 2]
    
    all_options = all_options.merge(
        valid_strikes[['date', 'cp_flag', 'tau']],
        on=['date', 'cp_flag', 'tau'],
        how='inner'
    )

    cleancalldata1 = all_options[(all_options['tau'] > 8) & (all_options['tau'] <= 365)]
    cleancalldata = (
        cleancalldata1
        .groupby(['date', 'cp_flag', 'tau', 'strike'], as_index=False)
        .agg(
            exdate=('exdate', 'max'),
            callprice=('callprice', lambda x: (x * cleancalldata1.loc[x.index, 'volume']).sum() / cleancalldata1.loc[x.index, 'volume'].sum()),
            volume=('volume', 'sum'),
            impliedVolatility=('impliedVolatility', 'mean'),
        )
    )
    indexdata_processed['date'] = pd.to_datetime(indexdata_processed['date']).dt.tz_localize(None)
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    
    index_filtered = indexdata_processed[
        (indexdata_processed['date'] >= start_date) &
        (indexdata_processed['date'] <= end_date)
    ]
    
    # Merge
    index_tr = pd.merge(index_filtered, df[['date', 'tr']], on='date', how='left')
    index_tr = index_tr.rename(columns={'snp': 'price'})
    index_tr_filled = index_tr.copy()
    index_tr_filled['tr'] = index_tr_filled['tr'].ffill()
    indexopt = pd.merge(cleancalldata, index_tr, on='date', how='inner')
    
    # Step 2: Keep only rows where 'tau' is not null
    indexopt = indexopt[indexopt['tau'].notna()]
    
    indexopt = indexopt[[
        'date',
        'price',
        'tr',
        'cp_flag',
        'strike',
        'callprice',
        'exdate',
        'tau',
        'volume',
        'impliedVolatility'
    ]].rename(columns={'impl_volatility': 'iv'})
    indexopt['date'] = pd.to_datetime(indexopt['date'], format='%Y%m%d')
    indexopt['tr'] = indexopt['tr'].ffill()
    
    indexopt['money'] = np.log(indexopt['strike'] * np.exp(-indexopt['tr'] * indexopt['tau'] / 252) / indexopt['price'])
    indexopt['money2'] = indexopt['strike'] / indexopt['price']
    
    
    indexopt = indexopt.sort_values(by=['date', 'cp_flag', 'exdate', 'strike']).reset_index(drop=True)
    indexopt2 = indexopt
    indexopt2['taurank0'] = indexopt2.groupby(['date', 'cp_flag'])['tau'] \
                                     .rank(method='dense')
    
    # Step 2: Filter out rows where tau is missing
    indexopt3 = indexopt2[indexopt2['tau'].notna()]
    
    # Step 3: Select specific columns and sort
    indexopt3 = indexopt3[[
        'date', 'cp_flag', 'exdate', 'tau', 'strike', 'price', 'tr', 
        'money', 'callprice', 'volume', 'impliedVolatility'
    ]].sort_values(by=['date', 'cp_flag', 'tau', 'strike']).reset_index(drop=True)
    indexopt3 = indexopt2[indexopt2['tau'].notna()][[
        'date', 'cp_flag', 'exdate', 'tau', 'strike', 'price', 'tr',
        'money', 'callprice', 'volume', 'impliedVolatility'
    ]].sort_values(by=['date', 'cp_flag', 'tau', 'strike']).reset_index(drop=True)
    
    indexopt3['delta'] = np.nan
    indexopt3['date'] = pd.to_datetime(indexopt3['date'], errors='coerce')
    indexopt3['date'] = indexopt3['date'].dt.strftime('%d%b%Y')
    indexopt3['exdate'] = pd.to_datetime(indexopt3['exdate'], errors='coerce')
    indexopt3['exdate'] = indexopt3['exdate'].dt.strftime('%d%b%Y')
    
    indexopt3['strike'] = pd.to_numeric(indexopt3['strike'], errors='coerce')
    indexopt3['tau'] = pd.to_numeric(indexopt3['tau'], errors='coerce')
    indexopt3['impliedVolatility'] = pd.to_numeric(indexopt3['impliedVolatility'], errors='coerce')
    
    def calculate_delta(S, K, tau, sigma, r, option_type):
        # Handle missing or invalid values
        if pd.isna(S) or pd.isna(K) or pd.isna(tau) or pd.isna(sigma) or pd.isna(r):
            return np.nan
        if tau <= 0 or sigma <= 0:
            return np.nan
    
        # Black-Scholes d1
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * tau) / (sigma * np.sqrt(tau))
    
        # Call vs Put delta
        if option_type.upper() == 'C':  
            return norm.cdf(d1)
        else:  
            return norm.cdf(d1) - 1
    
    # --- Apply to your dataset (indexopt3) ---
    # Convert tau from days → years (calendar, since tau is already exdate - date in days)
    indexopt3['tau_years'] = indexopt3['tau'] / 365
    indexopt3['strike'] = indexopt3['strike'] * 1000
    
    # Ensure numeric types
    cols_to_num = ['price', 'strike', 'tau_years', 'impliedVolatility', 'tr']
    indexopt3[cols_to_num] = indexopt3[cols_to_num].apply(pd.to_numeric, errors='coerce')
    
    # Calculate delta row-by-row
    indexopt3['delta'] = indexopt3.apply(
        lambda row: calculate_delta(
            S=row['price'],                 # underlying price per date
            K=row['strike'],                # strike
            tau=row['tau_years'],           # tau in years
            sigma=row['impliedVolatility'], # implied vol
            r=row['tr'],                    # risk-free rate
            option_type=row['cp_flag']      # call/put flag
        ),
        axis=1
    )
    indexopt3 = indexopt3.drop(columns=['tau_years'])
    
    optcpstats = indexopt3.groupby(['date', 'cp_flag', 'tau']).agg(
        n=('date', 'count'),
        minm=('money', 'min'),
        maxm=('money', 'max'),
        minstk=('strike', 'min'),
        maxstk=('strike', 'max')
    ).reset_index()
    indexopt3.columns = ['dateraw','cp_flag','exdateraw','tauday','X','s','tr','money','oprice','volume','iv','deltachk']

    optcount = indexopt3.groupby('dateraw').size().reset_index(name='count')
    optcount['date'] = pd.to_datetime(optcount['dateraw'], errors='coerce')
    optcount['date'] = optcount['date'].dt.strftime('%d%b%Y')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%d%b%Y')

    indexopt3 = indexopt3[indexopt3['dateraw'] == yesterday]
    optcount = optcount[optcount['date'] == yesterday]

    expected_count = optcount['count'].sum()  # total expected rows
    actual_count = indexopt3.shape[0]         # actual rows in indexopt3
    
    if expected_count != actual_count:
        raise ValueError(f"Mismatch: optcount={expected_count} rows, "
                         f"but indexopt3 has {actual_count} rows for {yesterday}")
    else:
        print(f"✅ Row count check passed: {actual_count} rows match optcount for {yesterday}")

    
    count_file = os.path.join(save_folder, f"{filesource}_count.csv")
    data_file = os.path.join(save_folder, f"{filesource}.csv")

    # Append optcount
    if os.path.exists(count_file):
        existing_count = pd.read_csv(count_file)
        optcount = pd.concat([existing_count, optcount], ignore_index=True)
        optcount.drop_duplicates(subset=["date"], keep="last", inplace=True)
    optcount.to_csv(count_file, index=False)

    # Append indexopt3
    if os.path.exists(data_file):
        existing_data = pd.read_csv(data_file)
        indexopt3 = pd.concat([existing_data, indexopt3], ignore_index=True)
        indexopt3.drop_duplicates(subset=["dateraw", "cp_flag", "tauday", "X"], keep="last", inplace=True)
    indexopt3.to_csv(data_file, index=False)

    print(f"✅ Finished updating {ticker_symbol}.")
