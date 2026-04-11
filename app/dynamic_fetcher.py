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
        
        years_data = []
        # Try to get up to 5 recent columns
        cols = list(inc.columns)[:5]
        
        for col in cols:
            year_str = str(col)[:4]
            
            def get_val(df, keys, m=1e6):
                if df.empty:
                    return 0.0
                for k in keys:
                    if k in df.index:
                        return float(df.loc[k, col]) / m
                return 0.0

            # --- Income Statement ---
            rev = get_val(inc, ['Total Revenue', 'Operating Revenue', 'Revenue'])
            net = get_val(inc, ['Net Income', 'Net Income Common Stockholders'])
            ebit = get_val(inc, ['EBIT', 'Operating Income'])
            cogs = get_val(inc, ['Cost Of Revenue', 'Cost of Goods Sold'])
            interest = get_val(inc, ['Interest Expense', 'Interest Expense Non Operating'])
            
            # --- Balance Sheet ---
            cash = get_val(bal, ['Cash And Cash Equivalents', 'Cash', 'Cash & Equivalents'])
            debt = get_val(bal, ['Total Debt', 'Long Term Debt And Capital Lease Obligation'])
            assets = get_val(bal, ['Total Assets'])
            equity = get_val(bal, ['Stockholders Equity', 'Total Stockholder Equity', 'Common Stock Equity'])
            
            current_assets = get_val(bal, ['Current Assets', 'Total Current Assets'])
            current_liabilities = get_val(bal, ['Current Liabilities', 'Total Current Liabilities'])
            accounts_receivable = get_val(bal, ['Accounts Receivable', 'Net Receivables'])
            inventory = get_val(bal, ['Inventory'])
            retained_earnings = get_val(bal, ['Retained Earnings'])
            
            # --- Cash Flow ---
            capex = get_val(cf, ['Capital Expenditure', 'Investments In Property Plant And Equipment'])
            # Capex is usually reported as a negative outflow, we want the absolute value
            capex = abs(capex) if capex != 0 else rev * 0.05
            
            # --- Approximations for missing generic fields ---
            ebitda = get_val(inc, ['EBITDA'])
            if ebitda == 0.0:
                da = get_val(cf, ['Depreciation And Amortization', 'Depreciation'])
                ebitda = ebit + da if da > 0 else ebit * 1.2
                
            working_cap = get_val(bal, ['Working Capital'])
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
