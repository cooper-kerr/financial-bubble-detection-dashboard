import os
import json
from process_stock import process_stock
from mat_generator.sbub_run import run_mat_generator
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
    yr1 = config.get("START_YEAR", "1996")
    yr2 = config.get("END_YEAR", "2023")
    
    # Get FRED API key from environment
    fred_api_key = os.environ.get('FRED_API_KEY')
    if not fred_api_key:
        print("FRED_API_KEY environment variable not set. The pipeline will not run.")
        return

    # Define data directories
    base_data_dir = "scripts-python/data"
    csv_dir = os.path.join(base_data_dir, "csv")
    mat_dir = os.path.join(base_data_dir, "mat")
    json_dir = os.path.join(base_data_dir, "json")

    # Create directories if they don't exist
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(mat_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    print("Starting the data pipeline...")

    for ticker in stock_list:
        print(f"\n{'='*50}")
        print(f"--- Processing Ticker: {ticker} ---")
        
        # 1. Process stock data and create CSV files
        process_stock(ticker, output_dir=csv_dir, fred_api_key=fred_api_key)
        
        # 2. Run MAT generator
        run_mat_generator(ticker, yr1, yr2, input_dir=csv_dir, output_dir=mat_dir)
        
        # 3. Convert MAT to JSON
        mat_to_json(ticker, yr1, yr2, input_dir=mat_dir, output_dir=json_dir)
        
        # 4. Upload JSON to Vercel
        # Note: This currently uses a placeholder function.
        # The user needs to complete the implementation in vercel_upload.py
        upload_file(ticker, data_dir=json_dir)
        
        print(f"--- Finished Ticker: {ticker} ---")
        print(f"{'='*50}\n")

    print("Data pipeline finished.")

if __name__ == "__main__":
    main()
