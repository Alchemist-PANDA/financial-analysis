import urllib.request
import urllib.error
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.sample_data import SEED_DATA

url = 'http://127.0.0.1:8000/api/analyze'
msft_data = SEED_DATA[0]
payload = {
    "company": {
        "company_name": msft_data["company_name"],
        "ticker": msft_data["ticker"]
    },
    "historical_data": msft_data["data"]["metrics"]["yearly"]
}
data = json.dumps(payload).encode('utf-8')
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'dev_default_key'
}
req = urllib.request.Request(url, data=data, headers=headers, method='POST')

print("Sending test request to /api/analyze...")
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("\nSUCCESS! Received response from FastAPI:")
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except urllib.error.URLError as e:
    print(f"Connection Error: {e.reason}")
