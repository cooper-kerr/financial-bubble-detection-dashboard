import os
import requests

def upload_file(json_path, ticker):
    """
    Uploads a specified JSON file to Vercel Blob Storage.
    """
    if not os.path.exists(json_path):
        print(f"JSON file not found at the provided path: {json_path}")
        return

    print(f"Uploading {json_path} to Vercel...")

    vercel_token = os.environ.get("VERCEL_TOKEN")
    if not vercel_token:
        print("VERCEL_TOKEN environment variable not set. Cannot upload.")
        return

    file_name = os.path.basename(json_path)

    # ==============================================================================
    # Vercel upload logic is now enabled.
    # The VERCEL_TOKEN environment variable must be scoped to the correct project.
    # ==============================================================================
    try:
        # The blob storage path can be organized by ticker for easier management.
        blob_path = f"data/{file_name}"
        api_url = f"https://blob.vercel-storage.com/{blob_path}"

        headers = {
            "Authorization": f"Bearer {vercel_token}",
            "x-api-version": "6", # Use a recent, stable API version
            # If your project is under a Vercel Team, add the teamId here:
            # "x-team-id": "YOUR_VERCEL_TEAM_ID"
        }

        with open(json_path, 'rb') as f:
            response = requests.put(api_url, headers=headers, data=f)

        response.raise_for_status()
        blob_data = response.json()
        print(f"Successfully uploaded {file_name} to Vercel Blob Storage.")
        print(f"Blob URL: {blob_data['url']}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to upload {file_name} to Vercel: {e}")
        if e.response:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # This standalone execution now requires the full path to the JSON file
        # and the ticker symbol as arguments.
        # e.g., python scripts-python/utils/vercel_upload.py /path/to/your/bubble_data_AAPL_2023.json AAPL
        json_file_path_arg = sys.argv[1]
        ticker_arg = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(json_file_path_arg).split('_')[2]
        upload_file(json_file_path_arg, ticker_arg)
    else:
        print("Please provide the full path to the JSON file and the ticker symbol.")
