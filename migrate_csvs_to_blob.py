import os, requests
from pathlib import Path

BLOB_TOKEN = "your_BLOB_READ_WRITE_TOKEN_here"
BASE_URL = "https://blob.vercel-storage.com"

for csv_file in Path("data/csv").glob("*.csv"):
    with open(csv_file, "rb") as f:
        content = f.read()
    r = requests.put(
        f"{BASE_URL}/csv/{csv_file.name}",
        headers={
            "Authorization": f"Bearer {BLOB_TOKEN}",
            "Content-Type": "text/csv",
            "x-content-type": "text/csv",
        },
        data=content
    )
    print(f"{'✅' if r.status_code in (200, 201) else '❌'} {csv_file.name} → HTTP {r.status_code}")
