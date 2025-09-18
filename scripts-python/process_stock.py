import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred
import os

def process_stock(ticker_symbol, output_dir="data", fred_api_key=None, start_year="1996"):
    """
    Fetches historical stock data, treasury data, and options data,
    processes it, and saves it to CSV files. Appends new data if
    existing files are found.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if fred_api_key is None:
        print("FRED API key not provided. Skipping treasury data.")
        return

    # Simplified filenames
    filesource = f"optout_{ticker_symbol}"
    count_file = os.path.join(output_dir, f"{filesource}_count.csv")
    data_file  = os.path.join(output_dir, f"{filesource}.csv")

    start_date = f"{start_year}-01-01"
    existing_data = None
    existing_count_data = None

    # Check for existing data and determine the new start date
    if os.path.exists(data_file):
        print(f"Existing data found for {ticker_symbol}. Reading last date.")
        try:
            existing_data = pd.read_csv(data_file)
            if not existing_data.empty:
                # Assuming the date column is named 'dateraw' and is in '%d%b%Y' format
                last_date_str = existing_data['dateraw'].iloc[-1]
                last_date = datetime.strptime(last_date_str, '%d%b%Y')
                start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
                print(f"New start date for fetching data: {start_date}")
            else:
                print("Existing data file is empty. Fetching full history.")
        except (KeyError, IndexError, pd.errors.EmptyDataError, ValueError) as e:
            print(f"Could not read or parse date from existing data file, will fetch full history. Error: {e}")
            existing_data = None # Reset to be safe

        if os.path.exists(count_file):
            try:
                existing_count_data = pd.read_csv(count_file)
            except pd.errors.EmptyDataError:
                print("Count file is empty.")
                existing_count_data = None
    else:
        print(f"No existing data found for {ticker_symbol}. Fetching full history from {start_date}.")

    end_date = datetime.now().strftime("%Y-%m-%d")
    
    if datetime.strptime(start_date, "%Y-%m-%d").date() >= datetime.now().date():
        print(f"Data for {ticker_symbol} is already up to date.")
        return

    print(f"Processing stock: {ticker_symbol} from {start_date} to {end_date}")

    # -------------------- Historical Data --------------------
    ticker = yf.Ticker(ticker_symbol)
    historical_data = ticker.history(start=start_date, end=end_date)
    if historical_data.empty:
        print(f"No new historical data found for {ticker_symbol}.")
        return

    closing_prices = historical_data[['Close']].reset_index()
    closing_prices.rename(columns={'Date': 'date', 'Close': 'snp'}, inplace=True)
    closing_prices['date'] = pd.to_datetime(closing_prices['date']).dt.tz_localize(None)
    indexdata_processed = closing_prices

    # -------------------- Treasury Data --------------------
    fred = Fred(api_key=fred_api_key)
    series_id = "DGS1MO"
    data = fred.get_series(series_id, start_date, end_date)
    
    df = pd.DataFrame(data, columns=["tr"])
    df.index.name = 'date'
    df = df.reset_index()
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    df['tr'] = df['tr'] / 100

    # -------------- Options Data ------------
    options_ticker = yf.Ticker(ticker_symbol)
    expirations = options_ticker.options
    today = datetime.now()
    
    expirations_this_year = [
        date for date in expirations
        if today <= datetime.strptime(date, '%Y-%m-%d') <= today + timedelta(days=365)
    ]
    
    all_options = pd.DataFrame()
    for expiration_date in expirations_this_year:
        try:
            options = options_ticker.option_chain(expiration_date)
            
            calls = options.calls.copy()
            calls['exdate'] = pd.to_datetime(expiration_date)
            calls['cp_flag'] = 'C'
            
            puts = options.puts.copy()
            puts['exdate'] = pd.to_datetime(expiration_date)
            puts['cp_flag'] = 'P'
            
            all_options = pd.concat([all_options, calls, puts], ignore_index=True)
            # print(f"Fetched options data for expiration date: {expiration_date}")
        except Exception as e:
            print(f"Error fetching options data for {expiration_date}: {e}")
    
    if all_options.empty:
        print(f"No new options data found for {ticker_symbol}")
        return

    all_options = all_options.rename(columns={'lastTradeDate': 'date'})
    all_options = all_options[['date', 'exdate', 'cp_flag', 'strike', 'bid', 'ask',
                               'volume', 'openInterest', 'impliedVolatility']]
    
    all_options['callprice'] = (all_options['bid'] + all_options['ask']) / 2
    all_options['date'] = all_options['date'].dt.date
    cols_to_convert = ['strike', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
    all_options[cols_to_convert] = all_options[cols_to_convert].apply(pd.to_numeric, errors='coerce')
    all_options['strike'] = all_options['strike'] / 1000
    all_options = all_options[all_options['volume'] > 0]
    all_options = all_options[(all_options['bid'] >= 0.05) | (all_options['ask'] >= 0.05)]
    all_options['date'] = pd.to_datetime(all_options['date']).dt.tz_localize(None)
    all_options['exdate'] = pd.to_datetime(all_options['exdate']).dt.tz_localize(None)
    all_options['tau'] = (all_options['exdate'] - all_options['date']).dt.days
    all_options = all_options[(all_options['tau'] > 8) & (all_options['tau'] <= 365)]
    all_options['tau_years'] = all_options['tau'] / 365
    
    def classify_maturity_group(tau_years):
        if tau_years <= 0.25: return '0-3M'
        elif tau_years <= 0.5: return '3-6M'
        else: return '6-12M'
    
    all_options['maturity_group'] = all_options['tau_years'].apply(classify_maturity_group)
    
    group_counts = all_options.groupby(['date', 'cp_flag', 'maturity_group']).size().reset_index(name='n_obs')
    valid_groups = group_counts[group_counts['n_obs'] >= 3]
    
    all_options = all_options.merge(
        valid_groups[['date', 'cp_flag', 'maturity_group']], 
        on=['date', 'cp_flag', 'maturity_group'], 
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
        (indexdata_processed['date'] >= pd.to_datetime(start_date)) &
        (indexdata_processed['date'] <= pd.to_datetime(end_date))
    ]
    
    index_tr = pd.merge(index_filtered, df[['date', 'tr']], on='date', how='left')
    index_tr = index_tr.rename(columns={'snp': 'price'})
    index_tr_filled = index_tr.copy()
    index_tr_filled['tr'] = index_tr_filled['tr'].ffill()
    indexopt = pd.merge(cleancalldata, index_tr_filled, on='date', how='inner')
    
    indexopt = indexopt[indexopt['tau'].notna()]
    
    indexopt = indexopt[[
        'date', 'price', 'tr', 'cp_flag', 'strike', 'callprice', 'exdate', 'tau', 'volume', 'impliedVolatility'
    ]].rename(columns={'impl_volatility': 'iv'})
    indexopt['date'] = pd.to_datetime(indexopt['date'])
    indexopt['tr'] = indexopt['tr'].ffill()
    
    indexopt['money'] = np.log(indexopt['strike'] * np.exp(-indexopt['tr'] * indexopt['tau'] / 252) / indexopt['price'])
    indexopt['money2'] = indexopt['strike'] / indexopt['price']
    
    indexopt = indexopt.sort_values(by=['date', 'cp_flag', 'exdate', 'strike']).reset_index(drop=True)
    indexopt2 = indexopt
    indexopt2['taurank0'] = indexopt2.groupby(['date', 'cp_flag'])['tau'].rank(method='dense')
    
    indexopt3 = indexopt2[indexopt2['tau'].notna()]
    
    indexopt3 = indexopt3[[
        'date', 'cp_flag', 'exdate', 'tau', 'strike', 'price', 'tr', 
        'money', 'callprice', 'volume', 'impliedVolatility'
    ]].sort_values(by=['date', 'cp_flag', 'tau', 'strike']).reset_index(drop=True)
    
    indexopt3['delta'] = np.nan
    indexopt3['date'] = pd.to_datetime(indexopt3['date']).dt.strftime('%d%b%Y')
    indexopt3['exdate'] = pd.to_datetime(indexopt3['exdate']).dt.strftime('%d%b%Y')
    
    indexopt3['strike'] = pd.to_numeric(indexopt3['strike'], errors='coerce')
    indexopt3['tau'] = pd.to_numeric(indexopt3['tau'], errors='coerce')
    indexopt3['impliedVolatility'] = pd.to_numeric(indexopt3['impliedVolatility'], errors='coerce')
    
    from scipy.stats import norm
    
    def calculate_delta(S, K, tau, sigma, r, option_type):
        if pd.isna(S) or pd.isna(K) or pd.isna(tau) or pd.isna(sigma) or pd.isna(r) or tau <= 0 or sigma <= 0:
            return np.nan
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * tau) / (sigma * np.sqrt(tau))
        return norm.cdf(d1) if option_type.upper() == 'C' else norm.cdf(d1) - 1
    
    indexopt3['tau_years'] = indexopt3['tau'] / 365
    cols_to_num = ['price', 'strike', 'tau_years', 'impliedVolatility', 'tr']
    indexopt3[cols_to_num] = indexopt3[cols_to_num].apply(pd.to_numeric, errors='coerce')
    
    indexopt3['delta'] = indexopt3.apply(
        lambda row: calculate_delta(
            S=row['price'], K=row['strike'], tau=row['tau_years'],
            sigma=row['impliedVolatility'], r=row['tr'], option_type=row['cp_flag']
        ),
        axis=1
    )
    indexopt3 = indexopt3.drop(columns=['tau_years'])
    
    def has_min_calls_and_puts(group, min_count=3):
        for _, tg in group.groupby('tau'):
            if (tg['cp_flag'] == 'C').sum() < min_count or (tg['cp_flag'] != 'C').sum() < min_count:
                return False
        return True

    indexopt3 = indexopt3.groupby('date').filter(has_min_calls_and_puts)
    if indexopt3.empty:
        print(f"No new data for {ticker_symbol} after filtering for minimum calls and puts.")
        return

    optcount = indexopt3.groupby('date').size().reset_index(name='count')
    optcount['date'] = pd.to_datetime(optcount['date']).dt.strftime('%d%b%Y')
    
    optcpstats = indexopt3.groupby(['date', 'cp_flag', 'tau']).agg(
        n=('date', 'count'), minm=('money', 'min'), maxm=('money', 'max'),
        minstk=('strike', 'min'), maxstk=('strike', 'max')
    ).reset_index()
    indexopt3.columns = ['dateraw','cp_flag','exdateraw','tauday','X','s','tr','money','oprice','volume','iv','deltachk']
    
    # --- Append new data to existing files ---
    if existing_data is not None:
        final_data = pd.concat([existing_data, indexopt3], ignore_index=True)
        final_data.drop_duplicates(subset=['dateraw', 'cp_flag', 'exdateraw', 'tauday', 'X'], keep='last', inplace=True)
        final_data = final_data.sort_values(by=['dateraw', 'cp_flag', 'exdateraw', 'X']).reset_index(drop=True)
    else:
        final_data = indexopt3

    if existing_count_data is not None:
        final_count_data = pd.concat([existing_count_data, optcount], ignore_index=True)
        final_count_data.drop_duplicates(subset=['date'], keep='last', inplace=True)
        final_count_data = final_count_data.sort_values(by=['date']).reset_index(drop=True)
    else:
        final_count_data = optcount

    final_count_data.to_csv(count_file, index=False)
    final_data.to_csv(data_file, index=False)
    
    print(f"Saved appended data for {ticker_symbol} to {output_dir}")

if __name__ == '__main__':
    fred_api_key = os.environ.get('FRED_API_KEY')
    if fred_api_key:
        process_stock('SPY', fred_api_key=fred_api_key)
    else:
        print("Please set the FRED_API_KEY environment variable to run this script.")
