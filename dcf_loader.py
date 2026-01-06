
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
if not EDGAR_IDENTITY:
    # Fallback to prevent crash (User Agent required by SEC)
    logger.warning("EDGAR_IDENTITY not found. Using fallback 'DCF_Valuation_App <no_email@example.com>'")
    EDGAR_IDENTITY = "DCF_Valuation_App <no_email@example.com>"
set_identity(EDGAR_IDENTITY)

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

# --- KEY CLASS 2: Edgar Fetcher (Financials) ---
    def get_financials_via_edgar(self):
        logger.info("Fetching Financial Statements from SEC Edgar...")
        try:
            company = Company(self.ticker)
        except Exception as e:
            raise ValueError(f"Edgar Init Failed: {e}")
            
        # These calls retrieve the standardized MultiPeriodStatement
        inc = company.income_statement()
        bal = company.balance_sheet()
        cf = company.cash_flow()
        
        # Convert to DataFrames
        return (
            inc.to_dataframe() if inc else pd.DataFrame(), 
            bal.to_dataframe() if bal else pd.DataFrame(), 
            cf.to_dataframe() if cf else pd.DataFrame()
        )

    def _get_edgar_series(self, df: pd.DataFrame, phrases: List[str], count: int = 3) -> List[float]:
        """
        Robustly finds a row in Edgar DataFrame by checking 'label' column and Index.
        Returns the data for the most recent 'count' years.
        """
        if df.empty:
            return [0.0] * count
            
        # 1. Identify Year Columns (keys starting with 'FY')
        year_cols = [c for c in df.columns if str(c).startswith('FY')]
        # Sort years descending (newest first)
        year_cols.sort(reverse=True, key=lambda x: str(x))
        target_years = year_cols[:count]
        
        matched_row = None
        
        # Normalize phrases for case-insensitive matching
        phrases = [p.lower() for p in phrases]
        
        # 2. Search by Label (Priority)
        if 'label' in df.columns:
            for phrase in phrases:
                # Exact match first
                mask = df['label'].astype(str).str.lower() == phrase
                if mask.any():
                    matched_row = df[mask].iloc[0]
                    break
                    
                # Contains match (secondary)
                mask = df['label'].astype(str).str.lower().str.contains(phrase, regex=False)
                if mask.any():
                    matched_row = df[mask].iloc[0]
                    break

        # 3. Search by Index (Concept Name) if no label match
        if matched_row is None:
            for phrase in phrases:
                 # Remove spaces for concept matching (e.g. "Gross Profit" -> "GrossProfit")
                 concept_phrase = phrase.replace(" ", "")
                 mask = df.index.astype(str).str.lower().str.contains(concept_phrase, regex=False)
                 if mask.any():
                     matched_row = df[mask].iloc[0]
                     break
                     
        if matched_row is None:
            return [0.0] * count
            
        # 4. Extract Values
        values = []
        for y in target_years:
            val = matched_row.get(y, 0.0)
            values.append(_safe_float(val))
            
        # Pad if missing years
        while len(values) < count:
            values.append(0.0)
            
        # Return oldest to newest (DCF expectation)
        return values[::-1]

    def _get_edgar_years(self, df: pd.DataFrame, count: int = 3) -> List[str]:
        if df.empty:
            return ["YYYY"] * count
        year_cols = [c for c in df.columns if str(c).startswith('FY')]
        year_cols.sort(reverse=True, key=lambda x: str(x))
        return year_cols[:count][::-1]

    def assemble(self) -> FinancialData:
        mkt = self.get_market_data()
        
        # 1. Try Edgar First (Official Data)
        try:
            inc, bal, cf = self.get_financials_via_edgar()
            if not inc.empty and not bal.empty:
                 logger.info("Using SEC Edgar Data.")
                 return self._process_edgar_data(inc, bal, cf, mkt)
        except Exception as e:
             logger.warning(f"Edgar Financials Failed: {e}")

        # 2. Fallback to YFinance (Live Data provider)
        try:
            inc, bal, cf = self.get_financials_via_yfinance()
            if not inc.empty and not bal.empty:
                 logger.info("Falling back to YFinance Data.")
                 return self._process_yfinance_data(inc, bal, cf, mkt)
        except Exception as e:
             logger.warning(f"YFinance Financials Failed: {e}")

        raise ValueError(f"Could not fetch data for {self.ticker} from Edgar or YFinance.")

    def _process_yfinance_data(self, inc, bal, cf, mkt) -> FinancialData:
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

    def _process_edgar_data(self, inc, bal, cf, mkt) -> FinancialData:
        # Mappings based on common US GAAP labels in Edgar
        years = self._get_edgar_years(inc)
        
        getter = self._get_edgar_series
        
        fd = FinancialData(
            years=years,
            revenue=getter(inc, ['Total Revenue', 'Revenues', 'Revenue']),
            ebit=getter(inc, ['Operating Income', 'Operating Profit', 'Operating Income (Loss)']),
            ebitda=getter(inc, ['Net Income', 'Net Loss']), # Approx starter, usually need to calc
            net_income=getter(inc, ['Net Income', 'Net Income (Loss)', 'Net Loss']),
            
            # Interest is tricky in standardized views, often net
            interest_expense=getter(inc, ['Interest Expense', 'Interest and Dividend Income']),
            
            # Balance Sheet
            current_assets=getter(bal, ['Total Current Assets', 'Current Assets']),
            current_liabilities=getter(bal, ['Total Current Liabilities', 'Current Liabilities']),
            cash_and_equivalents=getter(bal, ['Cash and Cash Equivalents', 'Cash']),
            
            # Debt is often split
            short_term_debt=getter(bal, ['Short-term Debt', 'Commercial Paper']),
            long_term_debt=getter(bal, ['Long-term Debt', 'Long-Term Debt']),
            total_debt=getter(bal, ['Total Debt']), # Often computed
            
            total_assets=getter(bal, ['Total Assets']),
            total_liabilities=getter(bal, ['Total Liabilities']),
            
            property_plant_equipment_net=getter(bal, ['Property, Plant and Equipment, Net', 'Net Property, Plant and Equipment']),
            preferred_equity=getter(bal, ['Preferred Stock']),
            
            # Cash Flow
            d_and_a=getter(cf, ['Depreciation, Depletion and Amortization', 'Depreciation']),
            capex=getter(cf, ['Payments to Acquire Property, Plant, and Equipment', 'Capital Expenditures']),
            preferred_dividends=getter(cf, ['Payment of Preferred Stock Dividends']),
            
            # Market Data (YF)
            shares_outstanding=float(mkt['shares']),
            beta=float(mkt['beta']),
            stock_price=float(mkt['price']),
            market_cap=float(mkt['market_cap']),
            risk_free_rate=float(mkt['treasury_yield']),
            market_return_rate=float(mkt['market_return'])
        )
        
        # Recalc helpers
        tax_prov = getter(inc, ['Income Tax Expense (Benefit)', 'Income Tax Provision'])
        pre_tax = getter(inc, ['Income (Loss) Before Income Taxes', 'Income Before Tax'])
        
        eff_rates = []
        for t, p in zip(tax_prov, pre_tax):
            if p != 0:
                eff_rates.append(t / p)
            else:
                eff_rates.append(0.21)
        fd.effective_tax_rate = eff_rates
        
        # Patch EBITDA if missing
        for i in range(3):
            if fd.ebitda[i] == 0:
                fd.ebitda[i] = fd.ebit[i] + fd.d_and_a[i]

        return fd


# Wrapper Logic Updated
def load_data_from_api(ticker: str) -> FinancialData:
    start_time = time.time()
    try:
        fetcher = HybridDataFetcher(ticker)
        data = fetcher.assemble()
        logger.info(f"Data Load Complete for {ticker} in {time.time() - start_time:.2f}s")
        return data
    except Exception as e:
        logger.critical(f"FATAL: All data sources failed for {ticker}. Error: {e}")
        raise RuntimeError(f"Could not load data for {ticker}. Details: {e}")

if __name__ == "__main__":
    # Test Block
    try:
        t = "MCD"
        print(f"Testing Loader for {t}...")
        d = load_data_from_api(t)
        print(f"Stock Price: ${d.stock_price}")
        print(f"Revenue (Last 3y): {d.revenue}")
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")

