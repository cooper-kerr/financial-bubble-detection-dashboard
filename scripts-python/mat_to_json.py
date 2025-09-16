import scipy.io
import json
import os
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def mat_to_json(ticker, data_dir="scripts-python/data"):
    """
    Converts a MAT file to a JSON file.
    """
    mat_path = os.path.join(data_dir, f"{ticker}.mat")
    json_path = os.path.join(data_dir, f"{ticker}.json")

    if not os.path.exists(mat_path):
        print(f"MAT file not found for {ticker} at {mat_path}")
        return

    print(f"Converting {mat_path} to {json_path}")
    try:
        mat_data = scipy.io.loadmat(mat_path)

        # The actual data is in a dictionary, need to clean it up
        clean_data = {}
        for key, value in mat_data.items():
            if not key.startswith('__'):
                # Squeeze singleton dimensions
                squeezed_value = np.squeeze(value)
                # Convert arrays to lists, handle single values
                if squeezed_value.ndim == 0:
                    clean_data[key] = squeezed_value.item()
                else:
                    # convert numpy array to list
                    clean_data[key] = squeezed_value.tolist()


        with open(json_path, 'w') as f:
            json.dump(clean_data, f, cls=NpEncoder)
        print(f"Successfully converted {mat_path} to {json_path}")
    except Exception as e:
        print(f"Failed to convert {ticker} MAT to JSON: {e}")

if __name__ == '__main__':
    import json
    with open('scripts-python/config.json', 'r') as f:
        config = json.load(f)

    stock_list = config.get("STOCK_LIST", [])
    data_directory = "scripts-python/data"

    for ticker in stock_list:
        mat_to_json(ticker, data_directory)
