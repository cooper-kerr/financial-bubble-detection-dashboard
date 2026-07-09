import os
from pathlib import Path
import yfinance as yf
import numpy as np
import pandas as pd
import hashlib
from datetime import datetime, timedelta
from fredapi import Fred
from scipy.stats import norm
import pytz
import time
import requests
import subprocess
from yahoo_csv_utils import merge_sort_option_data, rebuild_count_frame

# ---------------------------------------------------------------------------
# Vercel Blob configuration
# ---------------------------------------------------------------------------
BLOB_BASE_URL = os.getenv("BLOB_BASE_URL")          # public base URL of your Blob store
BLOB_TOKEN    = os.getenv("BLOB_READ_WRITE_TOKEN")   # read/write token stored in GitHub secrets
ROOT_DIR = Path(__file__).resolve().parent.parent
BLOB_CSV_UPLOADER = ROOT_DIR / "scripts" / "upload-csv-to-blob.ts"

def download_csv_from_blob(blob_path: str, local_path: str) -> bool:
    """
    Download a CSV from Vercel Blob to a local runner path.
    Returns True when the CSV was downloaded.
    """
    if not BLOB_BASE_URL:
        raise EnvironmentError("BLOB_BASE_URL environment variable is not set.")
    url = f"{BLOB_BASE_URL}/{blob_path}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(r.content)
            print(f"⬇️  Downloaded {blob_path} from Blob.")
            return True
        elif r.status_code == 404:
            print(f"⚠️  {blob_path} not found in Blob (status {r.status_code}).")
            return False
        else:
            raise RuntimeError(f"Unexpected status {r.status_code} fetching {blob_path}: {r.text}")
    except Exception as e:
        raise RuntimeError(f"Could not download {blob_path}: {e}") from e


def upload_csv_to_blob(local_path: str, blob_path: str) -> None:
    """
    Upload a local CSV to Vercel Blob, overwriting the existing file.
    Raises on any non-2xx response so the GitHub Action step fails visibly.
    """
    if not BLOB_TOKEN:
        raise EnvironmentError("BLOB_READ_WRITE_TOKEN environment variable is not set.")

    tsx_bin = ROOT_DIR / "node_modules" / ".bin" / "tsx"
    if tsx_bin.exists():
        command = [str(tsx_bin), str(BLOB_CSV_UPLOADER), local_path, blob_path]
    else:
        command = ["npx", "tsx", str(BLOB_CSV_UPLOADER), local_path, blob_path]

    result = subprocess.run(command, text=True, capture_output=True, timeout=120, cwd=ROOT_DIR)
    if result.returncode == 0:
        print(f"⬆️  Uploaded {local_path} → {result.stdout.strip()}")
    else:
        error_output = result.stderr.strip() or result.stdout.strip()
        if "Access denied" in error_output or "Token mismatch" in error_output:
            print(
                f"::warning::Skipping Blob CSV upload for {blob_path}; "
                f"the configured BLOB_READ_WRITE_TOKEN cannot write this Blob resource. "
                "The updated CSV will still be passed to the next job as a GitHub artifact."
            )
            return
        raise RuntimeError(f"Blob upload failed for {blob_path}: {error_output}")


def file_sha256(path: str) -> str | None:
    """
    Return the SHA-256 hash of a file if it exists, otherwise None.
    """
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# ---------------------------------------------------------------------------
# Ticker list & config  (unchanged)
# ---------------------------------------------------------------------------
Stockcode = [
    "SPX",
    "AAPL",
    "BAC",
    "C",
    "MSFT",
    "GE",
    "INTC",
    "CSCO",
    "BABA",
    "WFC",
    "JPM",
    "AMD",
    "META",
    "F",
    "TSLA",
    "GOOG",
    "T",
    "XOM",
    "AMZN",
    "MS",
    "NVDA",
    "AIG",
    "GM",
    "DIS",
    "BA",
]

csv_dir = "data/csv"   # local runner staging directory (temp, not committed to git)

YAHOO_SYMBOL_MAP = {
    "SPX": "^SPX",
}

def to_yahoo_symbol(symbol):
    return YAHOO_SYMBOL_MAP.get(symbol, symbol)

# ---------------------------------------------------------------------------
# FRED initialisation with retry  (unchanged)
# ---------------------------------------------------------------------------
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds

api_key = os.getenv("FRED_API_KEY")
if not api_key:
    raise ValueError("FRED_API_KEY environment variable not set")

for attempt in range(1, MAX_RETRIES + 1):
    try:
        fred = Fred(api_key=api_key)
        break
    except Exception as e:
        if attempt == MAX_RETRIES:
            raise RuntimeError(f"Failed to initialize FRED after {MAX_RETRIES} attempts") from e
        wait = RETRY_DELAY * attempt
        print(f"Attempt {attempt} failed: {e}. Retrying in {wait}s...")
        time.sleep(wait)

# ---------------------------------------------------------------------------
# Main loop  (all scraping/processing logic is unchanged)
# ---------------------------------------------------------------------------
for ticker_symbol in Stockcode:
    yahoo_symbol = to_yahoo_symbol(ticker_symbol)

    print(f"Running scraper for {ticker_symbol}...")

    filesource  = f"optout_{ticker_symbol}"
    save_folder = csv_dir
    os.makedirs(save_folder, exist_ok=True)

    ticker  = yf.Ticker(yahoo_symbol)
    eastern = pytz.timezone("US/Eastern")
    start_date = "1996-01-01"
    end_date   = (datetime.now(eastern) + timedelta(days=1)).strftime("%Y-%m-%d")

    historical_data = ticker.history(start=start_date, end=end_date)
    closing_prices  = historical_data[['Close']].reset_index()
    closing_prices.rename(columns={'Date': 'date', 'Close': 'snp'}, inplace=True)
    closing_prices['date'] = pd.to_datetime(closing_prices['date']).dt.tz_localize(None)
    indexdata_processed = closing_prices

    # ---- Treasury data ----
    series_id = "DGS1MO"
    data = fred.get_series(series_id, start_date, end_date)
    df = pd.DataFrame(data, columns=["tr"])
    df.index.name = 'date'
    df = df.reset_index()
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    df['tr'] = df['tr'] / 100

    # ---- Options data ----
    ticker      = yf.Ticker(yahoo_symbol)
    expirations = ticker.options
    today       = datetime.now()

    expirations_this_year = [
        date for date in expirations
        if today <= datetime.strptime(date, '%Y-%m-%d') <= today + timedelta(days=365)
    ]

    all_options = pd.DataFrame()
    for expiration_date in expirations_this_year:
        try:
            options = ticker.option_chain(expiration_date)

            calls = options.calls.copy()
            calls['exdate']  = pd.to_datetime(expiration_date)
            calls['cp_flag'] = 'C'

            puts = options.puts.copy()
            puts['exdate']  = pd.to_datetime(expiration_date)
            puts['cp_flag'] = 'P'

            all_options = pd.concat([all_options, calls, puts], ignore_index=True)
            print(f"Fetched options data for expiration date: {expiration_date}")
        except Exception as e:
            print(f"Error fetching options data for {expiration_date}: {e}")

    if all_options.empty:
        print(f"⏭️  No option chains returned for {ticker_symbol}; skipping ticker.")
        continue

    all_options = all_options.rename(columns={'lastTradeDate': 'date'})
    all_options = all_options[['date', 'exdate', 'cp_flag', 'strike', 'bid', 'ask',
                               'volume', 'openInterest', 'impliedVolatility']]

    all_options['callprice'] = (all_options['bid'] + all_options['ask']) / 2
    all_options['date']      = all_options['date'].dt.date
    cols_to_convert = ['strike', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
    all_options[cols_to_convert] = all_options[cols_to_convert].apply(pd.to_numeric, errors='coerce')
    all_options['strike'] = all_options['strike'] / 1000
    all_options = all_options[all_options['volume'] > 0]
    all_options = all_options[(all_options['bid'] >= 0.05) | (all_options['ask'] >= 0.05)]
    all_options['date']   = pd.to_datetime(all_options['date']).dt.tz_localize(None)
    all_options['exdate'] = pd.to_datetime(all_options['exdate']).dt.tz_localize(None)
    all_options['tau']    = (all_options['exdate'] - all_options['date']).dt.days
    all_options = all_options[(all_options['tau'] > 8) & (all_options['tau'] <= 365)]
    all_options['tau_years'] = all_options['tau'] / 365

    def classify_maturity_group(tau_years):
        if tau_years <= 0.25:
            return '0-3M'
        elif tau_years <= 0.5:
            return '3-6M'
        else:
            return '6-12M'

    all_options['maturity_group'] = all_options['tau_years'].apply(classify_maturity_group)

    group_counts  = all_options.groupby(['date', 'cp_flag', 'maturity_group']).size().reset_index(name='n_obs')
    valid_groups  = group_counts[group_counts['n_obs'] >= 3]
    all_options   = all_options.merge(
        valid_groups[['date', 'cp_flag', 'maturity_group']],
        on=['date', 'cp_flag', 'maturity_group'],
        how='inner'
    )

    strike_counts  = all_options.groupby(['date', 'cp_flag', 'tau'])['strike'].nunique().reset_index(name='n_strikes')
    valid_strikes  = strike_counts[strike_counts['n_strikes'] >= 2]
    all_options    = all_options.merge(
        valid_strikes[['date', 'cp_flag', 'tau']],
        on=['date', 'cp_flag', 'tau'],
        how='inner'
    )

    cleancalldata1 = all_options[(all_options['tau'] > 8) & (all_options['tau'] <= 365)]
    cleancalldata  = (
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

    index_tr       = pd.merge(index_filtered, df[['date', 'tr']], on='date', how='left')
    index_tr       = index_tr.rename(columns={'snp': 'price'})
    index_tr_filled = index_tr.copy()
    index_tr_filled['tr'] = index_tr_filled['tr'].ffill()
    indexopt       = pd.merge(cleancalldata, index_tr, on='date', how='inner')
    indexopt       = indexopt[indexopt['tau'].notna()]
    indexopt       = indexopt[[
        'date', 'price', 'tr', 'cp_flag', 'strike', 'callprice',
        'exdate', 'tau', 'volume', 'impliedVolatility'
    ]].rename(columns={'impl_volatility': 'iv'})

    indexopt['date'] = pd.to_datetime(indexopt['date'], format='%Y%m%d')
    indexopt['tr']   = indexopt['tr'].ffill()
    indexopt['money']  = np.log(indexopt['strike'] * np.exp(-indexopt['tr'] * indexopt['tau'] / 252) / indexopt['price'])
    indexopt['money2'] = indexopt['strike'] / indexopt['price']
    indexopt = indexopt.sort_values(by=['date', 'cp_flag', 'exdate', 'strike']).reset_index(drop=True)

    indexopt2 = indexopt
    indexopt2['taurank0'] = indexopt2.groupby(['date', 'cp_flag'])['tau'].rank(method='dense')
    indexopt3 = indexopt2[indexopt2['tau'].notna()][[
        'date', 'cp_flag', 'exdate', 'tau', 'strike', 'price', 'tr',
        'money', 'callprice', 'volume', 'impliedVolatility'
    ]].sort_values(by=['date', 'cp_flag', 'tau', 'strike']).reset_index(drop=True)

    indexopt3['delta'] = np.nan
    indexopt3['date']   = pd.to_datetime(indexopt3['date'], errors='coerce').dt.strftime('%d%b%Y')
    indexopt3['exdate'] = pd.to_datetime(indexopt3['exdate'], errors='coerce').dt.strftime('%d%b%Y')
    indexopt3['strike'] = pd.to_numeric(indexopt3['strike'], errors='coerce')
    indexopt3['tau']    = pd.to_numeric(indexopt3['tau'], errors='coerce')
    indexopt3['impliedVolatility'] = pd.to_numeric(indexopt3['impliedVolatility'], errors='coerce')

    def calculate_delta(S, K, tau, sigma, r, option_type):
        if pd.isna(S) or pd.isna(K) or pd.isna(tau) or pd.isna(sigma) or pd.isna(r):
            return np.nan
        if tau <= 0 or sigma <= 0:
            return np.nan
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * tau) / (sigma * np.sqrt(tau))
        return norm.cdf(d1) if option_type.upper() == 'C' else norm.cdf(d1) - 1

    indexopt3['tau_years'] = indexopt3['tau'] / 365
    indexopt3['strike']    = indexopt3['strike'] * 1000

    cols_to_num = ['price', 'strike', 'tau_years', 'impliedVolatility', 'tr']
    indexopt3[cols_to_num] = indexopt3[cols_to_num].apply(pd.to_numeric, errors='coerce')

    indexopt3['delta'] = indexopt3.apply(
        lambda row: calculate_delta(
            S=row['price'],
            K=row['strike'],
            tau=row['tau_years'],
            sigma=row['impliedVolatility'],
            r=row['tr'],
            option_type=row['cp_flag']
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

    indexopt3.columns = ['dateraw', 'cp_flag', 'exdateraw', 'tauday', 'x', 's', 'tr',
                         'money', 'oprice', 'volume', 'iv', 'deltachk']

    today_str = datetime.now(eastern).strftime('%d%b%Y')
    print(indexopt3.tail(5))
    indexopt3 = indexopt3[indexopt3['dateraw'] == today_str]
    optcount = indexopt3.groupby('dateraw').size().reset_index(name='count')

    expected_count = optcount['count'].sum()
    actual_count   = indexopt3.shape[0]
    if expected_count != actual_count:
        raise ValueError(
            f"Mismatch: optcount={expected_count} rows, "
            f"but indexopt3 has {actual_count} rows for {today_str}"
        )
    else:
        print(f"✅ Row count check passed: {actual_count} rows match optcount for {today_str}")

    # -----------------------------------------------------------------------
    # File paths  (local runner staging area — NOT committed to git)
    # -----------------------------------------------------------------------
    count_file = os.path.join(save_folder, f"{filesource}_count.csv")
    data_file  = os.path.join(save_folder, f"{filesource}.csv")

    # ⬇️  Pull the existing main CSV from Vercel Blob so we can append today's rows.
    # Count CSVs are derived locally and handed to the next workflow job as artifacts.
    if not os.path.exists(data_file):
        data_ok = download_csv_from_blob(f"csv/{filesource}.csv", data_file)
        if not data_ok:
            raise FileNotFoundError(
                f"Missing historical CSV for {ticker_symbol}: csv/{filesource}.csv. "
                "The daily pipeline requires Vercel Blob history and will not rebuild from only today's scrape."
            )
    else:
        print(f"📦 Using local artifact for {data_file}")

    data_hash_before = file_sha256(data_file)

    existing_data = pd.read_csv(data_file)
    indexopt3 = merge_sort_option_data(existing_data, indexopt3)
    optcount = rebuild_count_frame(indexopt3)
    indexopt3.to_csv(data_file, index=False)
    optcount.to_csv(count_file, index=False)

    # ⬆️  Push updated main CSV back to Vercel Blob only if content actually changed.
    # The derived count CSV remains local and is uploaded only as a GitHub Actions artifact.
    data_hash_after = file_sha256(data_file)

    if data_hash_before != data_hash_after:
        upload_csv_to_blob(data_file,  f"csv/{filesource}.csv")
    else:
        print(f"⏭️  No changes detected for csv/{filesource}.csv; skipping Blob upload.")

    print(f"✅ Finished updating {ticker_symbol}.")
