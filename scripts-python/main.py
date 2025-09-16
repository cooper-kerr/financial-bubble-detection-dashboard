import json
import os
from process_stock import process_stock
from csv_to_mat import csv_to_mat
from mat_to_json import mat_to_json
from utils.vercel_upload import upload_file

def main():
    """
    Orchestrates the entire data pipeline.
    """
    # Load configuration
    with open('scripts-python/config.json', 'r') as f:
        config = json.load(f)

    stock_list = config.get("STOCK_LIST", [])
    data_directory = "scripts-python/data"

    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    print("Starting the data pipeline...")

    for ticker in stock_list:
        print(f"--- Processing Ticker: {ticker} ---")

        # 1. Scrape and process stock data
        process_stock(ticker, data_directory)

        # 2. Convert CSV to MAT
        csv_to_mat(ticker, data_directory)

        # 3. Convert MAT to JSON
        mat_to_json(ticker, data_directory)

        # 4. Upload JSON to Vercel
        upload_file(ticker, data_directory)

        print(f"--- Finished Ticker: {ticker} ---\n")

    print("Data pipeline finished.")

if __name__ == "__main__":
    main()
