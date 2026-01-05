
import yfinance as yf
import pandas as pd

def test_yfinance_features():
    print("--- Testing yfinance Capabilities ---")
    ticker = yf.Ticker("AAPL")
    
    # 1. Income Statement
    print("\n[1] Income Statement (Top 3 rows):")
    try:
        inc = ticker.financials
        if not inc.empty:
            print(inc.head(3))
            print(f"   -> Columns (Dates): {list(inc.columns)}")
        else:
            print("   -> EMPTY")
    except Exception as e:
        print(f"   -> ERROR: {e}")

    # 2. Balance Sheet
    print("\n[2] Balance Sheet (Top 3 rows):")
    try:
        bal = ticker.balance_sheet
        if not bal.empty:
            print(bal.head(3))
        else:
            print("   -> EMPTY")
    except Exception as e:
        print(f"   -> ERROR: {e}")

    # 3. Ratios / Info
    print("\n[3] Ratios & Info (Sample):")
    try:
        info = ticker.info
        print(f"   -> Trailing P/E: {info.get('trailingPE')}")
        print(f"   -> Forward P/E:  {info.get('forwardPE')}")
        print(f"   -> Price/Book:   {info.get('priceToBook')}")
        print(f"   -> Beta:         {info.get('beta')}")
        print(f"   -> Dividend Yield:{info.get('dividendYield')}")
    except Exception as e:
        print(f"   -> ERROR: {e}")

if __name__ == "__main__":
    test_yfinance_features()
