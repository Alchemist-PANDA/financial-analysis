import yfinance as yf
import pandas as pd
import asyncio
from typing import Optional, Tuple

def fetch_historical_data_sync(ticker_symbol: str) -> Optional[Tuple[str, list]]:
    """
    Synchronously fetches up to 5 years of historical financial data for a given ticker
    using yfinance and norms it to the structure required by the Scorecard calculation.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # We need Income Statement, Balance Sheet, and Cash Flow
        income = stock.financials
        balance = stock.balance_sheet
        cashflow = stock.cashflow
        
        # If the ticker does not exist or has no financials, return None
        if income is None or income.empty:
            return None

        # stock.info can be None for invalid/delisted/rate-limited tickers
        stock_info = stock.info if isinstance(stock.info, dict) else {}
        company_name = stock_info.get("shortName", ticker_symbol)
        
        # Fill missing with 0 temporarily for math, but check bounds carefully
        inc = income.fillna(0)
        bal = balance.fillna(0) if (balance is not None and not balance.empty) else pd.DataFrame()
        cf = cashflow.fillna(0) if (cashflow is not None and not cashflow.empty) else pd.DataFrame()
        
        # Use balance sheet columns as the master column list (always annual).
        # Income statements can contain quarterly TTM columns that don't align.
        if not bal.empty:
            master_cols = list(bal.columns)[:5]
        else:
            master_cols = list(inc.columns)[:5]

        def find_nearest_col(df, target_col):
            """Find the column in df closest to target_col by date."""
            if df.empty:
                return None
            if target_col in df.columns:
                return target_col
            # Find nearest date column
            try:
                target_ts = pd.Timestamp(target_col)
                nearest = min(df.columns, key=lambda c: abs((pd.Timestamp(c) - target_ts).days))
                # Only use if within 6 months of the target
                if abs((pd.Timestamp(nearest) - target_ts).days) <= 180:
                    return nearest
            except Exception:
                pass
            return None

        years_data = []
        
        for master_col in master_cols:
            year_str = str(master_col)[:4]
            
            # Find the best matching column in each statement
            inc_col = find_nearest_col(inc, master_col)
            bal_col = master_col  # balance sheet IS the master
            cf_col = find_nearest_col(cf, master_col)
            
            def get_val(df, keys, col_to_use, m=1e6):
                if df.empty or col_to_use is None or col_to_use not in df.columns:
                    return 0.0
                for k in keys:
                    if k in df.index:
                        return float(df.loc[k, col_to_use]) / m
                return 0.0

            # --- Income Statement ---
            rev = get_val(inc, ['Total Revenue', 'Operating Revenue', 'Revenue'], inc_col)
            net = get_val(inc, ['Net Income', 'Net Income Common Stockholders'], inc_col)
            ebit = get_val(inc, ['EBIT', 'Operating Income'], inc_col)
            cogs = get_val(inc, ['Cost Of Revenue', 'Cost of Goods Sold'], inc_col)
            interest = get_val(inc, ['Interest Expense', 'Interest Expense Non Operating'], inc_col)
            
            # --- Balance Sheet ---
            cash = get_val(bal, ['Cash And Cash Equivalents', 'Cash', 'Cash & Equivalents'], bal_col)
            debt = get_val(bal, ['Total Debt', 'Long Term Debt And Capital Lease Obligation'], bal_col)
            assets = get_val(bal, ['Total Assets'], bal_col)
            equity = get_val(bal, ['Stockholders Equity', 'Total Stockholder Equity', 'Common Stock Equity'], bal_col)
            
            current_assets = get_val(bal, ['Current Assets', 'Total Current Assets'], bal_col)
            current_liabilities = get_val(bal, ['Current Liabilities', 'Total Current Liabilities'], bal_col)
            accounts_receivable = get_val(bal, ['Accounts Receivable', 'Net Receivables'], bal_col)
            inventory = get_val(bal, ['Inventory'], bal_col)
            retained_earnings = get_val(bal, ['Retained Earnings'], bal_col)
            
            # --- Cash Flow ---
            capex = get_val(cf, ['Capital Expenditure', 'Investments In Property Plant And Equipment'], cf_col)
            # Capex is usually reported as a negative outflow, we want the absolute value
            capex = abs(capex) if capex != 0 else rev * 0.05
            
            # --- Approximations for missing generic fields ---
            ebitda = get_val(inc, ['EBITDA'], inc_col)
            if ebitda == 0.0:
                da = get_val(cf, ['Depreciation And Amortization', 'Depreciation'], cf_col)
                ebitda = ebit + da if da > 0 else ebit * 1.2
                
            working_cap = get_val(bal, ['Working Capital'], bal_col)
            if working_cap == 0.0:
                if current_assets != 0 or current_liabilities != 0:
                    working_cap = current_assets - current_liabilities
                else:
                    working_cap = (assets * 0.3) - (debt * 0.2)
                    
            market_cap = stock_info.get("marketCap", 0) / 1e6
            
            years_data.append({
                'year': year_str,
                'revenue': round(rev, 2),
                'ebitda': round(ebitda, 2),
                'net_income': round(net, 2),
                'cash': round(cash, 2),
                'debt': round(abs(debt), 2),
                'total_assets': round(assets, 2),
                'equity': round(equity, 2),
                'working_capital': round(working_cap, 2),
                'retained_earnings': round(retained_earnings, 2) if retained_earnings != 0 else round(equity * 0.8, 2),
                'ebit': round(ebit, 2),
                'market_value_equity': round(market_cap, 2) if market_cap else round(equity * 2.0, 2),
                'accounts_receivable': round(accounts_receivable, 2),
                'inventory': round(inventory, 2),
                'capex': round(capex, 2),
                'cogs': round(cogs, 2),
                'interest_expense': round(abs(interest), 2),
                'current_assets': round(current_assets, 2),
                'current_liabilities': round(current_liabilities, 2)
            })
            
        # Reverse to chronological order (yfinance returns newest to oldest)
        years_data.reverse()
        
        # Remove zero-revenue ghost rows (quarterly TTM artifacts)
        years_data = [d for d in years_data if d['revenue'] > 0]
        
        # Deduplicate by year (keep the entry with the highest revenue)
        seen = {}
        for d in years_data:
            yr = d['year']
            if yr not in seen or d['revenue'] > seen[yr]['revenue']:
                seen[yr] = d
        years_data = sorted(seen.values(), key=lambda x: x['year'])
        
        # Pad data if we have less than 5 years but more than 0
        if 0 < len(years_data) < 5:
            oldest_year_data = years_data[0].copy()
            for i in range(5 - len(years_data)):
                padded_data = oldest_year_data.copy()
                # Decrement the year strings for the padded data
                padded_data['year'] = str(int(oldest_year_data['year']) - (i + 1))
                years_data.insert(0, padded_data)
        
        # Quick validation
        if len(years_data) == 0:
            return None
            
        return company_name, years_data
        
    except Exception as e:
        print(f"[DYNAMIC FETCHER ERROR] Failed fetching {ticker_symbol}: {str(e)}")
        return None

async def fetch_historical_data(ticker_symbol: str) -> Optional[Tuple[str, list]]:
    """
    Async wrapper for yfinance fetching.
    """
    return await asyncio.to_thread(fetch_historical_data_sync, ticker_symbol)
