
import yfinance as yf
t = yf.Ticker("AAPL")
print("--- Income Statement Keys ---")
try:
    print(t.financials.index.tolist())
except:
    print("Error fetching financials")

print("\n--- Balance Sheet Keys ---")
try:
    print(t.balance_sheet.index.tolist())
except:
    print("Error fetching balance sheet")
