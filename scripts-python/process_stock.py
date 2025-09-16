import yfinance as yf
import pandas as pd
import json
import os

def process_stock(ticker, data_dir="scripts-python/data"):
    """
    Downloads historical stock data, calculates the daily price change,
    and saves it to a CSV file.
    """
    print(f"Processing stock: {ticker}")
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")  # 1 year of historical data
        if hist.empty:
            print(f"No data found for ticker: {ticker}")
            return

        hist['change'] = hist['Close'].diff()

        output_path = os.path.join(data_dir, f"{ticker}.csv")
        hist.to_csv(output_path)
        print(f"Saved data for {ticker} to {output_path}")

    except Exception as e:
        print(f"Failed to process {ticker}: {e}")

if __name__ == '__main__':
    with open('scripts-python/config.json', 'r') as f:
        config = json.load(f)

    stock_list = config.get("STOCK_LIST", [])
    data_directory = "scripts-python/data"

    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    for ticker in stock_list:
        process_stock(ticker, data_directory)
