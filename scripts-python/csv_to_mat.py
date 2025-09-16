import pandas as pd
from scipy.io import savemat
import os

def csv_to_mat(ticker, data_dir="scripts-python/data"):
    """
    Converts a CSV file to a MAT file.
    """
    csv_path = os.path.join(data_dir, f"{ticker}.csv")
    mat_path = os.path.join(data_dir, f"{ticker}.mat")

    if not os.path.exists(csv_path):
        print(f"CSV file not found for {ticker} at {csv_path}")
        return

    print(f"Converting {csv_path} to {mat_path}")
    try:
        df = pd.read_csv(csv_path)
        # Convert dataframe to a dictionary of numpy arrays for savemat
        mat_dict = {col: df[col].values for col in df.columns}

        # Special handling for object type columns (like 'Date')
        for col in df.columns:
            if df[col].dtype == 'object':
                mat_dict[col] = df[col].to_numpy().astype('U')

        savemat(mat_path, mat_dict)
        print(f"Successfully converted {csv_path} to {mat_path}")
    except Exception as e:
        print(f"Failed to convert {ticker} CSV to MAT: {e}")

if __name__ == '__main__':
    import json
    with open('scripts-python/config.json', 'r') as f:
        config = json.load(f)

    stock_list = config.get("STOCK_LIST", [])
    data_directory = "scripts-python/data"

    for ticker in stock_list:
        csv_to_mat(ticker, data_directory)
