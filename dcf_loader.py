
import os
import time
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from edgar import Company, set_identity

# Import the data class from dcf_code
from dcf_code import FinancialData

# --- HTTP Session with Timeout and Retries ---
HTTP_TIMEOUT = (3.05, 15)  # (connect, read) seconds

def create_session_with_retry():
    """Create a requests session with retry logic and timeout"""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Global session for reuse
_http_session = create_session_with_retry()

# --- Configuration & Setup ---
load_dotenv('.env')

# 1. Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("dcf_loader")

# 2. Configure Edgartools Identity
EDGAR_IDENTITY = os.getenv("EDGAR_IDENTITY")
if EDGAR_IDENTITY:
    set_identity(EDGAR_IDENTITY)
else:
    logger.warning("EDGAR_IDENTITY not found. Edgartools may fail.")

# 3. Configure Local Storage for Edgartools (Speed Boost)
if os.getenv("EDGAR_USE_LOCAL_DATA", "False").lower() == "true":
    logger.info("Edgartools Local Data Caching: ENABLED (Expect faster repeat runs)")

# --- Caching Layer (Market Data) ---
CACHE_FILE = "/tmp/market_data_cache.json" # Use /tmp for Vercel/Lambda read-write consistency
CACHE_EXPIRY_HOURS = 24

def load_cache() -> Dict[str, Any]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    return {}

def save_cache(cache: Dict[str, Any]):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")

def get_cached_market_data(ticker: str) -> Optional[Dict[str, Any]]:
    cache = load_cache()
    if ticker in cache:
        entry = cache[ticker]
        cached_time = datetime.fromisoformat(entry['timestamp'])
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600
        if age_hours < CACHE_EXPIRY_HOURS:
            logger.info(f"Using Cached Market Data for {ticker} (Age: {age_hours:.1f}h)")
            return entry['data']
    return None

def set_cached_market_data(ticker: str, data: Dict[str, Any]):
    cache = load_cache()
    cache[ticker] = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    save_cache(cache)


# --- Helper Functions ---

def _safe_float(val, default=0.0):
    try:
        if isinstance(val, (pd.Series, list)):
            val = val[0] if len(val) > 0 else default
        if val is None or pd.isna(val):
            return default
        return float(val)
    except:
        return default

def _get_series_from_row(df: pd.DataFrame, tags: List[str], count: int = 3) -> List[float]:
    """
    Tries to find a row in the DataFrame matching one of the 'tags'.
    Returns the most recent 'count' values as a list of floats.
    """
    matched_row = None
    
    for tag in tags:
        if tag in df.index:
            candidate = df.loc[tag]
            if candidate.fillna(0).abs().sum() > 0:
                matched_row = candidate
                break
            
    if matched_row is None:
        return [0.0] * count

    # Extract values
    values = matched_row.head(count).values.tolist()
    
    clean_values = []
    for v in values:
        clean_values.append(_safe_float(v))
        
    while len(clean_values) < count:
        clean_values.append(0.0)
        
    return clean_values[::-1]

def _get_dates_from_cols(df: pd.DataFrame, count: int = 3) -> List[str]:
    cols = df.columns[:count]
    dates = []
    for c in cols:
        try:
            dates.append(str(c.year) if hasattr(c, 'year') else str(c)[:4])
        except:
            dates.append("Unknown")
    return dates[::-1]

# --- KEY CLASS 1: Hybrid Fetcher (Preferred) ---
class HybridDataFetcher:
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.yf_ticker = yf.Ticker(self.ticker)
        self.company = Company(self.ticker)
        
    def get_market_data(self) -> Dict[str, Any]:
        cached = get_cached_market_data(self.ticker)
        if cached:
            return cached
            
        logger.info(f"Fetching Live Market Data for {self.ticker}...")
        try:
            info = self.yf_ticker.info
            data = {
                "price": info.get('currentPrice') or info.get('regularMarketPreviousClose') or 0.0,
                "beta": info.get('beta', 1.0),
                "shares": info.get('sharesOutstanding', 0),
                "market_cap": info.get('marketCap', 0),
                "treasury_yield": 0.042,
                "market_return": 0.10,
            }
            # Fetch treasury yield with timeout
            try:
                tnx = yf.Ticker("^TNX")
                hist = tnx.history(period="1d", timeout=10)
                if not hist.empty:
                    data["treasury_yield"] = hist['Close'].iloc[-1] / 100
            except Exception:
                pass
                
            set_cached_market_data(self.ticker, data)
            return data
        except Exception as e:
            logger.error(f"YFinance Market Data Error: {e}")
            raise

    def get_financials_via_yfinance(self):
        logger.info("Fetching Financial Statements (Standardized via YFinance)...")
        inc = self.yf_ticker.financials
        bal = self.yf_ticker.balance_sheet
        cf = self.yf_ticker.cashflow
        return inc, bal, cf

    def assemble(self) -> FinancialData:
        mkt = self.get_market_data()
        inc, bal, cf = self.get_financials_via_yfinance()
        
        if inc.empty or bal.empty:
            raise ValueError(f"Could not fetch data for {self.ticker}. Ticker might be delisted or invalid.")

        rev_tags = ['Total Revenue', 'Operating Revenue', 'Revenue']
        ebit_tags = ['EBIT', 'Operating Income', 'Operating Profit']
        ebitda_tags = ['EBITDA', 'Normalized EBITDA']
        net_inc_tags = ['Net Income', 'Net Income Common Stockholders']
        tax_tags = ['Tax Provision', 'Income Tax Expense']
        int_exp_tags = ['Interest Expense', 'Interest Expense Non Operating']
        
        ca_tags = ['Total Current Assets', 'Current Assets']
        cl_tags = ['Total Current Liabilities', 'Current Liabilities']
        cash_tags = ['Cash And Cash Equivalents', 'Cash']
        std_tags = ['Current Debt', 'Short Term Debt', 'Commercial Paper']
        ltd_tags = ['Long Term Debt']
        td_tags = ['Total Debt']
        ta_tags = ['Total Assets']
        tl_tags = ['Total Liabilities']
        ppe_tags = ['Net PPE', 'Plant Property Equipment Net', 'Property Plant And Equipment Net']
        pref_tags = ['Preferred Stock', 'Preferred Stock Equity']
        
        da_tags = ['Depreciation And Amortization', 'Reconciled Depreciation']
        capex_tags = ['Capital Expenditure', 'Capital Expenditures'] 
        
        years = _get_dates_from_cols(inc)
        
        fd = FinancialData(
            years=years,
            revenue=_get_series_from_row(inc, rev_tags),
            ebit=_get_series_from_row(inc, ebit_tags),
            ebitda=_get_series_from_row(inc, ebitda_tags),
            net_income=_get_series_from_row(inc, net_inc_tags),
            effective_tax_rate=[], 
            interest_expense=_get_series_from_row(inc, int_exp_tags),
            
            current_assets=_get_series_from_row(bal, ca_tags),
            current_liabilities=_get_series_from_row(bal, cl_tags),
            cash_and_equivalents=_get_series_from_row(bal, cash_tags),
            short_term_debt=_get_series_from_row(bal, std_tags),
            long_term_debt=_get_series_from_row(bal, ltd_tags),
            total_debt=_get_series_from_row(bal, td_tags),
            total_assets=_get_series_from_row(bal, ta_tags),
            total_liabilities=_get_series_from_row(bal, tl_tags),
            property_plant_equipment_net=_get_series_from_row(bal, ppe_tags),
            preferred_equity=_get_series_from_row(bal, pref_tags),
            
            d_and_a=_get_series_from_row(cf, da_tags),
            capex=_get_series_from_row(cf, capex_tags),
            preferred_dividends=[],
            
            shares_outstanding=float(mkt['shares']),
            beta=float(mkt['beta']),
            stock_price=float(mkt['price']),
            market_cap=float(mkt['market_cap']),
            risk_free_rate=float(mkt['treasury_yield']),
            market_return_rate=float(mkt['market_return'])
        )
        
        tax_vals = _get_series_from_row(inc, tax_tags)
        inc_vals = _get_series_from_row(inc, ['Pretax Income', 'Income Before Tax'])
        
        eff_rates = []
        for t, i in zip(tax_vals, inc_vals):
            if i != 0:
                eff_rates.append(t / i)
            else:
                eff_rates.append(0.21)
        fd.effective_tax_rate = eff_rates

        return fd

# --- KEY CLASS 2: FMP Fetcher (Backup) ---
class FMPDataFetcher:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY not found. Cannot use FMP backup.")
        self.base_url = "https://financialmodelingprep.com/stable"

    def _safe_request(self, url: str):
        """Robust request handler with timeout, rate limiting, and retries"""
        try:
            # Respect Rate Limits
            time.sleep(0.2) 
            response = _http_session.get(url, timeout=HTTP_TIMEOUT)
            
            if response.status_code == 429:
                logger.warning("FMP Rate Limit Exceeded. Waiting 1s...")
                time.sleep(1.0)
                response = _http_session.get(url, timeout=HTTP_TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "Error Message" in data:
                    logger.error(f"FMP API Error: {data['Error Message']}")
                    return []
                return data
            
            logger.error(f"FMP Request failed: {response.status_code} for {url}")
            return []
        except requests.Timeout:
            logger.error(f"FMP request timed out: {url}")
            return []
        except Exception as e:
            logger.error(f"FMP Connection error: {e}")
            return []

    def get_market_return(self) -> float:
        return 0.10 # Fallback 10%

    def get_financial_data(self, ticker: str) -> FinancialData:
        logger.info(f"FMP BACKUP: Fetching {ticker} (Stable Endpoint)...")
        
        # 1. Financials
        inc_url = f"{self.base_url}/income-statement?symbol={ticker}&limit=5&apikey={self.api_key}"
        bal_url = f"{self.base_url}/balance-sheet-statement?symbol={ticker}&limit=5&apikey={self.api_key}"
        cf_url  = f"{self.base_url}/cash-flow-statement?symbol={ticker}&limit=5&apikey={self.api_key}"
        
        inc_stmt = self._safe_request(inc_url)
        bal_sheet = self._safe_request(bal_url)
        cf_stmt = self._safe_request(cf_url)
        
        if not inc_stmt or not bal_sheet:
            raise ValueError("FMP: Critical financial data could not be fetched.")

        # 2. Market Data
        quote_url = f"{self.base_url}/quote?symbol={ticker}&apikey={self.api_key}"
        prof_url  = f"{self.base_url}/profile?symbol={ticker}&apikey={self.api_key}"
        
        quote_data = self._safe_request(quote_url)
        profile_data = self._safe_request(prof_url)
        
        quote = quote_data[0] if quote_data else {}
        profile = profile_data[0] if profile_data else {}
        
        # 3. Helpers
        def get_series(data_list, key, count=3):
            selected = data_list[:count]
            values = [float(x.get(key, 0) or 0) for x in selected]
            return values[::-1]
            
        def get_dates(data_list, key='calendarYear', count=3):
            subset = data_list[:count]
            return [str(x.get(key, "")) for x in subset][::-1]

        # 4. Tax Rate
        tax_expense = [float(x.get('incomeTaxExpense', 0) or 0) for x in inc_stmt[:3]]
        pre_tax_inc = [float(x.get('incomeBeforeTax', 0) or 0) for x in inc_stmt[:3]]
        
        eff_tax_rate = []
        for t, i in zip(tax_expense, pre_tax_inc):
            rate = t / i if i != 0 else 0.21
            eff_tax_rate.append(rate)
        eff_tax_rate = eff_tax_rate[::-1]

        # 5. Shares & Price
        q_shares = float(quote.get('sharesOutstanding') or 0)
        q_mkt_cap = float(quote.get('marketCap') or 0)
        q_price = float(quote.get('price') or 0)
        p_mkt_cap = float(profile.get('marketCap') or 0)
        p_price = float(profile.get('price') or 0)
        
        market_cap_val = q_mkt_cap if q_mkt_cap > 0 else p_mkt_cap
        stock_price_val = q_price if q_price > 0 else p_price
        
        if q_shares > 0:
            shares_val = q_shares
        elif market_cap_val > 0 and stock_price_val > 0:
            shares_val = market_cap_val / stock_price_val
        else:
            shares_val = 0.0

        # 6. Map
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
            risk_free_rate=0.042, # Fallback
            market_return_rate=0.10
        )

# --- Wrapper Function (Failover Logic) ---
def load_data_from_api(ticker: str) -> FinancialData:
    start_time = time.time()
    
    # Attempt 1: Hybrid (Edgar/YF)
    try:
        fetcher = HybridDataFetcher(ticker)
        data = fetcher.assemble()
        logger.info(f"Hybrid Data Load Complete for {ticker} in {time.time() - start_time:.2f}s")
        return data
    except Exception as e:
        logger.warning(f"Hybrid Fetch Failed: {e}. Attempting Failover to FMP...")
    
    # Attempt 2: FMP Backup
    try:
        fmp = FMPDataFetcher() # Loads API key from env
        data = fmp.get_financial_data(ticker)
        logger.info(f"FMP Backup Load Complete for {ticker}")
        return data
    except Exception as e:
        logger.critical(f"ALL DATA SOURCES FAILED for {ticker}. Error: {e}")
        raise RuntimeError(f"Could not load data for {ticker} from any source.")

if __name__ == "__main__":
    # Test Block
    try:
        t = "AAPL"
        print(f"Testing Loader for {t}...")
        d = load_data_from_api(t)
        print(f"Stock Price: ${d.stock_price}")
        print(f"Revenue (Last 3y): {d.revenue}")
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")

