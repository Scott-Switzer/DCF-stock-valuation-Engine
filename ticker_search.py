"""
Ticker Search Module
Dynamic yfinance-backed search with caching and rate limiting
"""
import yfinance as yf
import time
import hashlib
from functools import lru_cache
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# --- In-Memory Cache (24h TTL) ---
_search_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_HOURS = 24

def _get_cache_key(query: str) -> str:
    """Normalize query and generate cache key"""
    normalized = query.strip().upper()
    return hashlib.md5(normalized.encode()).hexdigest()

def _get_cached_results(query: str) -> Optional[List[Dict]]:
    """Check in-memory cache for results"""
    key = _get_cache_key(query)
    if key in _search_cache:
        entry = _search_cache[key]
        age = datetime.now() - entry['timestamp']
        if age < timedelta(hours=CACHE_TTL_HOURS):
            logger.info(f"Cache HIT for '{query}' (age: {age.total_seconds()/3600:.1f}h)")
            return entry['data']
        else:
            del _search_cache[key]
    return None

def _set_cached_results(query: str, results: List[Dict]):
    """Store results in cache"""
    key = _get_cache_key(query)
    _search_cache[key] = {
        'timestamp': datetime.now(),
        'data': results
    }
    # Prune old entries if cache gets too large
    if len(_search_cache) > 1000:
        _prune_cache()

def _prune_cache():
    """Remove expired entries"""
    now = datetime.now()
    expired = [k for k, v in _search_cache.items() 
               if now - v['timestamp'] > timedelta(hours=CACHE_TTL_HOURS)]
    for k in expired:
        del _search_cache[k]

# --- Rate Limiting ---
_rate_limit: Dict[str, List[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 30     # max requests per window per IP

def check_rate_limit(ip: str) -> bool:
    """Returns True if request is allowed, False if rate limited"""
    now = time.time()
    
    if ip not in _rate_limit:
        _rate_limit[ip] = []
    
    # Remove old timestamps
    _rate_limit[ip] = [t for t in _rate_limit[ip] if now - t < RATE_LIMIT_WINDOW]
    
    if len(_rate_limit[ip]) >= RATE_LIMIT_MAX:
        return False
    
    _rate_limit[ip].append(now)
    return True

# --- yfinance Search ---
def search_tickers(query: str, limit: int = 12) -> List[Dict[str, Any]]:
    """
    Search for tickers using yfinance.
    Returns list of: {symbol, shortname, exchange, type, score}
    """
    if not query or len(query) < 2:
        return []
    
    # Check cache first
    cached = _get_cached_results(query)
    if cached is not None:
        return cached[:limit]
    
    try:
        logger.info(f"yfinance search for: '{query}'")
        
        # Use yfinance's search functionality
        search = yf.Search(query, max_results=limit, news_count=0)
        
        results = []
        
        # Process quotes (main results)
        if hasattr(search, 'quotes') and search.quotes:
            for item in search.quotes[:limit]:
                results.append({
                    'symbol': item.get('symbol', ''),
                    'shortname': item.get('shortname', item.get('longname', '')),
                    'exchange': item.get('exchange', ''),
                    'type': item.get('quoteType', 'EQUITY'),
                    'score': item.get('score', 0)
                })
        
        # Cache results
        _set_cached_results(query, results)
        
        return results[:limit]
        
    except Exception as e:
        logger.error(f"yfinance search failed: {e}")
        return []

# --- Fallback: Static list for common tickers ---
COMMON_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "JNJ",
    "WMT", "PG", "MA", "UNH", "HD", "DIS", "PYPL", "NFLX", "INTC", "VZ",
    "ADBE", "CRM", "CMCSA", "PFE", "KO", "PEP", "T", "MRK", "ABT", "CSCO"
]

def fallback_search(query: str, limit: int = 12) -> List[Dict[str, Any]]:
    """Fallback to static list if yfinance fails"""
    query = query.upper().strip()
    matches = [t for t in COMMON_TICKERS if t.startswith(query)]
    return [{'symbol': t, 'shortname': '', 'exchange': '', 'type': 'EQUITY', 'score': 0} 
            for t in matches[:limit]]
