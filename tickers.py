"""
Stock Ticker Database for DCF Valuation Engine

This module provides a curated list of NYSE and NASDAQ tickers.
Structure is designed for easy replacement with dynamic API in the future.

To update with dynamic data:
    1. Uncomment the fetch_tickers_from_api() function
    2. Replace get_all_tickers() to call the API
    3. Add caching to avoid repeated API calls
"""

# Curated list of ~500 most commonly analyzed stocks (S&P 500 + popular tech/growth)
# Full list of 6000+ available via NASDAQ FTP: ftp://ftp.nasdaqtrader.com/SymbolDirectory/

TICKERS = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSM", "AVGO", "ORCL",
    "CRM", "ADBE", "ACN", "CSCO", "IBM", "INTC", "AMD", "QCOM", "TXN", "NOW",
    "AMAT", "MU", "LRCX", "ADI", "KLAC", "SNPS", "CDNS", "MRVL", "NXPI", "FTNT",
    "PANW", "CRWD", "ZS", "NET", "DDOG", "SNOW", "PLTR", "TEAM", "MDB", "WDAY",
    "VEEV", "SPLK", "OKTA", "ZM", "DOCU", "U", "RBLX", "COIN", "PATH", "S",
    
    # Finance
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "SPGI",
    "CME", "ICE", "MCO", "COF", "DFS", "V", "MA", "PYPL", "SQ", "FIS",
    "FISV", "ADP", "PAYX", "BRK.A", "BRK.B", "TRV", "PGR", "ALL", "AIG", "MET",
    "PRU", "AFL", "CB", "HIG", "LNC", "TROW", "BEN", "IVZ", "NTRS", "STT",
    
    # Healthcare
    "UNH", "JNJ", "PFE", "ABBV", "MRK", "LLY", "TMO", "DHR", "ABT", "BMY",
    "AMGN", "GILD", "VRTX", "REGN", "MRNA", "ISRG", "MDT", "SYK", "BSX", "EW",
    "ZBH", "DXCM", "IDXX", "A", "IQV", "MTD", "WAT", "WST", "BIO", "TECH",
    "HCA", "CVS", "CI", "ELV", "HUM", "CNC", "MOH", "UHS", "THC", "GEHC",
    
    # Consumer Discretionary
    "TSLA", "HD", "NKE", "MCD", "SBUX", "LOW", "TGT", "COST", "TJX", "ROST",
    "BKNG", "ABNB", "MAR", "HLT", "ORLY", "AZO", "CMG", "DHI", "LEN", "NVR",
    "GM", "F", "RIVN", "LCID", "YUM", "DPZ", "DRI", "WYNN", "LVS", "MGM",
    "LULU", "NKE", "VFC", "PVH", "GOOS", "RL", "TPR", "CROX", "DECK", "BIRK",
    
    # Consumer Staples
    "PG", "KO", "PEP", "WMT", "PM", "MO", "MDLZ", "CL", "KMB", "GIS",
    "K", "HSY", "SJM", "CAG", "CPB", "HRL", "TSN", "KHC", "STZ", "BF.B",
    "EL", "CLX", "CHD", "WBA", "KR", "SYY", "COST", "DG", "DLTR", "WMT",
    
    # Energy
    "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "OXY", "PXD",
    "DVN", "HES", "FANG", "HAL", "BKR", "KMI", "WMB", "OKE", "ET", "EPD",
    
    # Industrials
    "HON", "UNP", "UPS", "CAT", "RTX", "LMT", "BA", "GE", "DE", "MMM",
    "GD", "NOC", "TT", "EMR", "ROK", "ITW", "PH", "ETN", "PCAR", "CTAS",
    "FAST", "WM", "RSG", "ODFL", "CSX", "NSC", "FDX", "DAL", "UAL", "LUV",
    
    # Materials
    "LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "NUE", "STLD", "CLF",
    "VMC", "MLM", "CRH", "DOW", "LYB", "PPG", "ALB", "FMC", "MOS", "CF",
    
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "WEC", "ES",
    "ED", "FE", "PPL", "EIX", "DTE", "ETR", "AEE", "CMS", "CNP", "NI",
    
    # Real Estate
    "PLD", "AMT", "EQIX", "PSA", "WELL", "SPG", "O", "DLR", "CCI", "AVB",
    "EQR", "VTR", "ARE", "BXP", "SLG", "VNO", "KIM", "REG", "FRT", "HST",
    
    # Communication Services
    "DIS", "CMCSA", "NFLX", "T", "VZ", "TMUS", "CHTR", "EA", "TTWO", "WBD",
    "PARA", "FOX", "FOXA", "LYV", "IPG", "OMC", "MTCH", "SNAP", "PINS", "SPOT",
    
    # ETFs (Popular for comparison)
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VEA", "VWO", "BND", "GLD",
    "SLV", "XLF", "XLE", "XLK", "XLV", "XLI", "ARKK", "ARKG", "XBI", "SMH",
]

def get_all_tickers():
    """
    Returns list of all available tickers.
    
    Future Enhancement:
        Replace with dynamic API call to NASDAQ FTP or similar:
        ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt
        ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt
    """
    return sorted(set(TICKERS))

def search_tickers(query: str, limit: int = 10):
    """
    Search tickers by prefix match.
    
    Args:
        query: Search string (e.g., "APP" returns "AAPL", "APPS")
        limit: Maximum results to return
        
    Returns:
        List of matching ticker symbols
    """
    if not query:
        return []
    
    query = query.upper().strip()
    all_tickers = get_all_tickers()
    
    # Prioritize exact matches and prefix matches
    matches = []
    for t in all_tickers:
        if t.startswith(query):
            matches.append(t)
        if len(matches) >= limit:
            break
            
    return matches

# For future dynamic implementation:
# def fetch_tickers_from_api():
#     """Fetch latest tickers from NASDAQ FTP"""
#     import ftplib
#     import io
#     
#     ftp = ftplib.FTP('ftp.nasdaqtrader.com')
#     ftp.login()
#     ftp.cwd('SymbolDirectory')
#     
#     # Read NASDAQ listed
#     nasdaq_data = io.BytesIO()
#     ftp.retrbinary('RETR nasdaqlisted.txt', nasdaq_data.write)
#     nasdaq_data.seek(0)
#     
#     # Parse pipe-delimited file
#     tickers = []
#     for line in nasdaq_data.read().decode('utf-8').split('\n')[1:]:
#         if '|' in line:
#             symbol = line.split('|')[0]
#             if symbol and symbol != 'File Creation Time':
#                 tickers.append(symbol)
#     
#     ftp.quit()
#     return tickers
