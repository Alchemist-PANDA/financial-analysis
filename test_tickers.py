"""Quick test for dynamic fetcher fixes."""
from app.dynamic_fetcher import fetch_historical_data_sync

for ticker in ['TM', 'BABA', 'AAPL']:
    print(f"\n--- Testing {ticker} ---")
    result = fetch_historical_data_sync(ticker)
    if result:
        name, data = result
        print(f"  Name: {name}")
        print(f"  Years returned: {len(data)}")
        for d in data:
            print(f"    {d['year']}: rev={d['revenue']}, ebitda={d['ebitda']}, equity={d['equity']}")
    else:
        print(f"  RETURNED NONE - fetch failed")

# Now test calculator on the results
print("\n\n--- Testing calculator on BABA data ---")
result = fetch_historical_data_sync('BABA')
if result:
    name, data = result
    from app.calculator import calculate_metrics
    try:
        metrics = calculate_metrics(data)
        print(f"  Calculator SUCCESS: {len(metrics['yearly'])} years of metrics")
        print(f"  Revenue CAGR: {metrics['revenue_cagr_pct']}%")
        print(f"  Altman Z: {metrics['current_z_score']}")
    except Exception as e:
        print(f"  Calculator FAILED: {e}")

print("\n\n--- Testing calculator on TM data ---")
result = fetch_historical_data_sync('TM')
if result:
    name, data = result
    from app.calculator import calculate_metrics
    try:
        metrics = calculate_metrics(data)
        print(f"  Calculator SUCCESS: {len(metrics['yearly'])} years of metrics")
    except Exception as e:
        print(f"  Calculator FAILED: {e}")
else:
    print("  Cannot test calculator - TM fetch returned None")
