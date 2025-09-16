import os
import requests

def upload_file(ticker, data_dir="scripts-python/data"):
    """
    Uploads a JSON file to Vercel Blob Storage.
    """
    json_path = os.path.join(data_dir, f"{ticker}.json")

    if not os.path.exists(json_path):
        print(f"JSON file not found for {ticker} at {json_path}")
        return

    print(f"Uploading {json_path} to Vercel...")

    vercel_token = os.environ.get("VERCEL_TOKEN")
    if not vercel_token:
        print("VERCEL_TOKEN environment variable not set. Cannot upload.")
        return

    # ==============================================================================
    # TODO: UNCOMMENT AND EDIT THE FOLLOWING BLOCK TO ENABLE VERCEL UPLOAD
    #
    # You will need to replace `YOUR_VERCEL_PROJECT_ID` with your actual
    # Vercel project ID. You can find this in your Vercel project settings.
    # If you are using a team, you might also need to provide a teamId.
    #
    # See Vercel Blob Storage documentation for more details:
    # https://vercel.com/docs/storage/vercel-blob/using-the-blob-api
    #
    # --- START OF BLOCK TO EDIT ---
    #
    # try:
    #     file_name = f"{ticker}.json"
    #     api_url = f"https://blob.vercel-storage.com/{file_name}"
    #
    #     headers = {
    #         "Authorization": f"Bearer {vercel_token}",
    #         "x-api-version": "6", # Use a recent, stable API version
    #         # Add teamId if your project is under a Vercel Team
    #         # "x-team-id": "YOUR_VERCEL_TEAM_ID"
    #     }
    #
    #     with open(json_path, 'rb') as f:
    #         response = requests.put(
    #             api_url,
    #             headers=headers,
    #             data=f,
    #             params={"pathname": f"data/{file_name}"} # Optional: organize in a subfolder
    #         )
    #
    #     response.raise_for_status()
    #     blob_data = response.json()
    #     print(f"Successfully uploaded {file_name} to Vercel Blob Storage.")
    #     print(f"Blob URL: {blob_data['url']}")
    #
    # except requests.exceptions.RequestException as e:
    #     print(f"Failed to upload {file_name} to Vercel: {e}")
    #     if e.response:
    #         print(f"Response status code: {e.response.status_code}")
    #         print(f"Response body: {e.response.text}")
    #
    # --- END OF BLOCK TO EDIT ---
    # ==============================================================================

    # If you have not implemented the upload logic, this placeholder will be printed.
    if 'blob_data' not in locals():
        print("Placeholder: Vercel upload logic is commented out. Please edit this script to enable it.")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        # To test, you need to set the VERCEL_TOKEN environment variable
        # export VERCEL_TOKEN="your_token_here"
        # python scripts-python/utils/vercel_upload.py AAPL
        upload_file(ticker)
    else:
        print("Please provide a ticker symbol.")
