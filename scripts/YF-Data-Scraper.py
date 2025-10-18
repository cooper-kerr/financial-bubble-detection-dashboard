import os
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred
from scipy.stats import norm

# Directory where CSV files live
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

    # ---------------- Stock Price Data ----------------
    ticker = yf.Ticker(ticker_symbol)
    historical_data = ticker.history(start=start_date, end=end_date)
    closing_prices = historical_data[['Close']].reset_index()
    closing_prices.rename(columns={'Date': 'date', 'Close': 'snp'}, inplace=True)
    closing_prices['date'] = pd.to_datetime(closing_prices['date']).dt.tz_localize(None)
    indexdata_processed = closing_prices

    # ---------------- Treasury Data ----------------
    series_id = "DGS1MO"
    data = fred.get_series(series_id, start_date, end_date)
    df = pd.DataFrame(data, columns=["tr"])
    df.index.name = 'date'
    df = df.reset_index()
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    df['tr'] = df['tr'] / 100

    # ---------------- Options Data ----------------
    expirations = ticker.options
    today = datetime.now()
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
            print(f"Fetched options for {expiration_date}")
        except Exception as e:
            print(f"Error fetching options for {expiration_date}: {e}")

    if all_options.empty:
        print(f"No options data for {ticker_symbol}, skipping...")
        continue

    # ---------------- Clean Options Data ----------------
    all_options = all_options.rename(columns={'lastTradeDate': 'date'})
    all_options = all_options[['date', 'exdate', 'cp_flag', 'strike', 'bid', 'ask',
                               'volume', 'openInterest', 'impliedVolatility']]
    all_options['callprice'] = (all_options['bid'] + all_options['ask']) / 2
    all_options['date'] = pd.to_datetime(all_options['date']).dt.tz_localize(None)
    all_options['exdate'] = pd.to_datetime(all_options['exdate']).dt.tz_localize(None)
    cols_to_convert = ['strike', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
    all_options[cols_to_convert] = all_options[cols_to_convert].apply(pd.to_numeric, errors='coerce')
    all_options['strike'] = all_options['strike'] / 1000
    all_options = all_options[(all_options['volume'] > 0) & ((all_options['bid'] >= 0.05) | (all_options['ask'] >= 0.05))]
    all_options['tau'] = (all_options['exdate'] - all_options['date']).dt.days
    all_options = all_options[(all_options['tau'] > 8) & (all_options['tau'] <= 365)]
    all_options['tau_years'] = all_options['tau'] / 365

    # Maturity groups
    def classify_maturity_group(tau_years):
        if tau_years <= 0.25:
            return '0-3M'
        elif tau_years <= 0.5:
            return '3-6M'
        else:
            return '6-12M'
    all_options['maturity_group'] = all_options['tau_years'].apply(classify_maturity_group)

    group_counts = all_options.groupby(['date', 'cp_flag', 'maturity_group']).size().reset_index(name='n_obs')
    valid_groups = group_counts[group_counts['n_obs'] >= 3]
    all_options = all_options.merge(valid_groups[['date', 'cp_flag', 'maturity_group']],
                                    on=['date', 'cp_flag', 'maturity_group'], how='inner')

    # Aggregate clean options
    cleancalldata1 = all_options
    cleancalldata = (
        cleancalldata1
        .groupby(['date', 'cp_flag', 'tau', 'strike'], as_index=False)
        .agg(
            exdate=('exdate', 'max'),
            callprice=('callprice', lambda x: (x * cleancalldata1.loc[x.index, 'volume']).sum() / cleancalldata1.loc[x.index, 'volume'].sum()),
            volume=('volume', 'sum'),
            impliedVolatility=('impliedVolatility', 'mean')
        )
    )

    # ---------------- Merge with index data ----------------
    index_tr = pd.merge(indexdata_processed, df[['date', 'tr']], on='date', how='left')
    index_tr.rename(columns={'snp': 'price'}, inplace=True)
    index_tr['tr'] = index_tr['tr'].ffill()
    indexopt = pd.merge(cleancalldata, index_tr, on='date', how='inner')
    indexopt = indexopt[indexopt['tau'].notna()]

    # ---------------- Compute extra columns ----------------
    indexopt['money'] = np.log(indexopt['strike'] * np.exp(-indexopt['tr'] * indexopt['tau'] / 252) / indexopt['price'])
    indexopt['money2'] = indexopt['strike'] / indexopt['price']

    # Sort and rank
    indexopt = indexopt.sort_values(['date','cp_flag','exdate','strike']).reset_index(drop=True)
    indexopt['taurank0'] = indexopt.groupby(['date','cp_flag'])['tau'].rank(method='dense')

    indexopt3 = indexopt.copy()
    indexopt3['delta'] = np.nan
    indexopt3['date'] = pd.to_datetime(indexopt3['date']).dt.strftime('%d%b%Y')
    indexopt3['exdate'] = pd.to_datetime(indexopt3['exdate']).dt.strftime('%d%b%Y')

    # ---------------- Append to CSVs ----------------
    optcount = indexopt3.groupby('date').size().reset_index(name='count')

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
        indexopt3.drop_duplicates(subset=["date","cp_flag","tau","strike"], keep="last", inplace=True)
    indexopt3.to_csv(data_file, index=False)

    print(f"✅ Finished updating {ticker_symbol}.")
