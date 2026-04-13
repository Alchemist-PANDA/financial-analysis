import requests

url = "https://ghouri112-financial-terminal-backend.hf.space/api/explain-chart?ticker=AAPL"
try:
    print(f"Requesting: {url}")
    res = requests.get(url, timeout=30)
    print(f"Status Code: {res.status_code}")
    print(f"Content-Type: {res.headers.get('Content-Type')}")
    print(f"Response Body: {res.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
