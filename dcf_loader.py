import requests
from datetime import datetime, timedelta
from typing import List, Optional
from dcf_code import FinancialData

import requests
import time
from datetime import datetime, timedelta
from typing import List, Optional
from dcf_code import FinancialData

import requests
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Optional
from dcf_code import FinancialData

# Load environment variables from keys.env
load_dotenv('keys.env')

class FMPDataFetcher:
    def __init__(self, api_key: str = None):
        # Use passed key or fetch from environment
        self.api_key = api_key or os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("API Key not found. Please set FMP_API_KEY in keys.env or pass it explicitly.")
            
        # UPDATED: Use the 'stable' base URL for legacy/restricted plans
        self.base_url = "https://financialmodelingprep.com/stable"

    def _safe_request(self, url: str):
        """Helper to handle rate limits and errors gracefully."""
        try:
            # Stable endpoint might have stricter rate limits? Keeping safe sleep.
            time.sleep(0.5) 
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "Error Message" in data:
                    print(f"API Error for {url}: {data['Error Message']}")
                    return []
                return data
            
            print(f"Request failed with status {response.status_code} for {url}")
            return []
        except Exception as e:
            print(f"Connection error: {e}")
            return []

    def get_market_return(self) -> float:
        """
        Attempts to calculate S&P 500 return.
        NOTE: 'stable' endpoint does not seem to support historical-price-full (Returns 404).
        We will return the fallback 10% immediately to avoid wasting API calls/errors 
        until a working historical endpoint is found.
        """
        # Fallback to 10.0% (Long term avg)
        print("   Using Default Market Return (10%) - Historical Data Restricted on 'Stable' plan.")
        return 0.10

    def get_financial_data(self, ticker: str) -> FinancialData:
        print(f"Fetching Financials for {ticker} (Stable Endpoint)...")
        
        # 1. Fetch Financial Statements
        # URL Pattern: .../stable/income-statement?symbol=AAPL&limit=5...
        
        inc_url = f"{self.base_url}/income-statement?symbol={ticker}&limit=5&apikey={self.api_key}"
        bal_url = f"{self.base_url}/balance-sheet-statement?symbol={ticker}&limit=5&apikey={self.api_key}"
        cf_url  = f"{self.base_url}/cash-flow-statement?symbol={ticker}&limit=5&apikey={self.api_key}"
        
        inc_stmt = self._safe_request(inc_url)
        bal_sheet = self._safe_request(bal_url)
        cf_stmt = self._safe_request(cf_url)
        
        if not inc_stmt or not bal_sheet:
            print("❌ Critical: Income Statement or Balance Sheet failed to load.")
            raise ValueError("Critical financial data could not be fetched. Check API Key or Ticker.")

        # 2. Fetch Market Data & Profile
        # Note: Quote/Profile endpoints verified to work on 'stable'
        quote_url = f"{self.base_url}/quote?symbol={ticker}&apikey={self.api_key}"
        prof_url  = f"{self.base_url}/profile?symbol={ticker}&apikey={self.api_key}"
        
        quote_data = self._safe_request(quote_url)
        profile_data = self._safe_request(prof_url)
        
        quote = quote_data[0] if quote_data else {}
        profile = profile_data[0] if profile_data else {}
        
        # 3. Fetch Treasury (Risk Free Rate)
        # 'stable/treasury' returned 404 in tests. v3/treasury returns 403.
        # Defaulting to 4.2% (Current approx 10y yield)
        print("   Using Default Risk Free Rate (4.2%) - Treasury Data Restricted.")
        rf_rate = 0.042
        
        # 4. Market Return
        market_return = self.get_market_return()

        # Helper to extract last 3 years (Order: Oldest -> Newest)
        def get_series(data_list, key, count=3):
            selected = data_list[:count]
            values = [float(x.get(key, 0) or 0) for x in selected]
            return values[::-1]
            
        def get_dates(data_list, key='calendarYear', count=3):
            subset = data_list[:count]
            return [str(x.get(key, "")) for x in subset][::-1]

        # Calculate Tax Rate
        tax_expense = [float(x.get('incomeTaxExpense', 0) or 0) for x in inc_stmt[:3]]
        pre_tax_inc = [float(x.get('incomeBeforeTax', 0) or 0) for x in inc_stmt[:3]]
        
        eff_tax_rate = []
        for t, i in zip(tax_expense, pre_tax_inc):
            rate = t / i if i != 0 else 0.21
            eff_tax_rate.append(rate)
        eff_tax_rate = eff_tax_rate[::-1]

        # Calculated Fields
        # Shares: Quote often relies on calculations in 'stable' endpoint
        q_shares = float(quote.get('sharesOutstanding') or 0)
        q_mkt_cap = float(quote.get('marketCap') or 0)
        q_price = float(quote.get('price') or 0)
        
        p_mkt_cap = float(profile.get('marketCap') or 0) # Key is 'marketCap' not 'mktCap'
        p_price = float(profile.get('price') or 0)
        
        # Best Market Cap
        market_cap_val = q_mkt_cap if q_mkt_cap > 0 else p_mkt_cap
        
        # Best Price
        stock_price_val = q_price if q_price > 0 else p_price
        
        # Calculate Shares if missing
        if q_shares > 0:
            shares_val = q_shares
        elif market_cap_val > 0 and stock_price_val > 0:
            shares_val = market_cap_val / stock_price_val
        else:
            shares_val = 0.0

        # Map to FinancialData class
        return FinancialData(
            years=get_dates(inc_stmt, 'calendarYear'),
            revenue=get_series(inc_stmt, 'revenue'),
            ebit=get_series(inc_stmt, 'operatingIncome'),
            ebitda=get_series(inc_stmt, 'ebitda'),
            net_income=get_series(inc_stmt, 'netIncome'),
            effective_tax_rate=eff_tax_rate,
            interest_expense=get_series(inc_stmt, 'interestExpense'),
            
            current_assets=get_series(bal_sheet, 'totalCurrentAssets'),
            current_liabilities=get_series(bal_sheet, 'totalCurrentLiabilities'),
            cash_and_equivalents=get_series(bal_sheet, 'cashAndCashEquivalents'),
            short_term_debt=get_series(bal_sheet, 'shortTermDebt'),
            long_term_debt=get_series(bal_sheet, 'longTermDebt'),
            total_debt=get_series(bal_sheet, 'totalDebt'),
            total_assets=get_series(bal_sheet, 'totalAssets'),
            total_liabilities=get_series(bal_sheet, 'totalLiabilities'),
            property_plant_equipment_net=get_series(bal_sheet, 'propertyPlantEquipmentNet'),
            preferred_equity=get_series(bal_sheet, 'preferredStock'),
            
            d_and_a=get_series(cf_stmt, 'depreciationAndAmortization'),
            capex=get_series(cf_stmt, 'capitalExpenditure'),
            preferred_dividends=get_series(cf_stmt, 'dividendsPaid'),
            
            shares_outstanding=shares_val,
            beta=float(profile.get('beta', 1.0) or 1.0),
            stock_price=stock_price_val,
            market_cap=market_cap_val,
            risk_free_rate=rf_rate,
            market_return_rate=market_return
        )

# Simple functional wrapper
def load_data_from_api(ticker: str) -> FinancialData:
    fetcher = FMPDataFetcher() # Key loaded from env automatically
    return fetcher.get_financial_data(ticker)

if __name__ == "__main__":
    # Test
    try:
        data = load_data_from_api("AAPL")
        print(f"Revenue: {data.revenue}")
        print(f"S&P 500 CAGR: {data.market_return_rate:.2%}")
    except Exception as e:
        print(f"Test Failed: {e}")
