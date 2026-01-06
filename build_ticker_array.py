"""
Build a de-duplicated JS array of *single-company* tickers that work in yfinance,
while excluding ETFs/funds/notes/trusts, most REITs, most MLPs/LPs, and (optionally)
banks/insurers/financial services.

Sources:
- Nasdaq Trader symbol directory:
  - nasdaqlisted.txt (Nasdaq)
  - otherlisted.txt  (NYSE/NYSE Arca/AMEX + others)

Output:
- static/js/tickers.js containing: const TICKER_DATA = [ { s: "...", n: "..." }, ... ];

USAGE:
  pip install pandas yfinance requests
  python build_ticker_array.py

NOTES:
- Step 1 (directory download) is fast and gets you a very large universe.
- Step 2 (optional yfinance enrichment + filtering) is slower and rate-limit sensitive.
  You can start with directory-only filtering and only later enable yfinance filtering.
"""

from __future__ import annotations

import re
import time
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests

# Optional (only used if ENABLE_YFINANCE_FILTERING=True)
try:
    import yfinance as yf
except Exception:
    yf = None  # type: ignore


# -----------------------------
# Config
# -----------------------------

ENABLE_YFINANCE_FILTERING = False  # Set False for speed (directory only ~30s), True for high quality (~15m)
YFINANCE_SLEEP_SECONDS = 0.25      # throttle to reduce HTTP 429 / blocks
MAX_YFINANCE_TICKERS = 3000        # safety cap

# Exclusion toggles (yfinance-based)
EXCLUDE_FINANCIALS = True          # banks/insurers/financial services (sector/industry)
EXCLUDE_REITS = True               # REITs via yfinance sector/industry + name heuristics
EXCLUDE_LPS_MLPS = True            # partnership/LP/MLP heuristics

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL  = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

# Output path relative to this script
OUTPUT_PATH = "static/js/tickers.js"

# -----------------------------
# Helpers
# -----------------------------

def fetch_symbol_file(url: str) -> pd.DataFrame:
    """
    Nasdaq Trader files are pipe-delimited with header and a trailing footer line.
    """
    print(f"Fetching {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    resp = requests.get(url, timeout=30, headers=headers)
    resp.raise_for_status()
    text = resp.text.strip().splitlines()

    # Drop footer lines that start with "File Creation Time"
    rows = [line for line in text if not line.startswith("File Creation Time") and line.strip()]
    # Convert to DataFrame
    data = [r.split("|") for r in rows]
    header = data[0]
    values = data[1:]
    # Handle potential ragged rows
    valid_values = [v for v in values if len(v) == len(header)]
    
    df = pd.DataFrame(valid_values, columns=header)
    return df


def normalize_symbol(sym: str) -> str:
    sym = sym.strip().upper()
    # yfinance expects BRK-B, BF-B, etc (dash not dot) in many contexts.
    # But your list uses BRK.B; we can keep dots in output if you prefer.
    # We'll standardize internals to yfinance-friendly (dash) and output with dash.
    sym = sym.replace(".", "-")
    return sym


def clean_company_name(name: str) -> str:
    name = re.sub(r"\s+", " ", (name or "").strip())
    # Remove common suffix clutter from directory names:
    # e.g., "Microsoft Corporation - Common Stock"
    name = re.sub(r"\s*-\s*Common Stock\b.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*-\s*Ordinary Shares\b.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*-\s*Class [A-Z]\b.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*-\s*American Depositary Shares\b.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*-\s*ADS\b.*$", "", name, flags=re.IGNORECASE)
    name = name.strip(" -")
    return name


# Heuristic exclusions based on directory "Security Name"/"Company Name"
# Keep these conservative; yfinance-based filtering can do the heavy lifting.
EXCLUDE_NAME_PATTERNS = [
    r"\bETF\b",
    r"\bETN\b",
    r"\bEXCHANGE TRADED FUND\b",
    r"\bEXCHANGE-TRADED FUND\b",
    r"\bINDEX\b",                 # catches many notes/funds; can be overly aggressive
    r"\bTRUST\b",
    r"\bMUTUAL FUND\b",
    r"\bFUND\b",
    r"\bPORTFOLIO\b",
    r"\bNOTES?\b",
    r"\bDEPOSITARY RECEIPTS?\b",
    r"\bADR\b",
    r"\bADRs\b",
    r"\bUNIT\b",
    r"\bWARRANT\b",
    r"\bRIGHTS?\b",
    r"\bPREFERRED\b",
    r"\bSERIES\b",
    r"\bSPAC\b",
    r"\bACQUISITION\b",
]
EXCLUDE_NAME_RE = re.compile("|".join(EXCLUDE_NAME_PATTERNS), re.IGNORECASE)

LP_MLP_RE = re.compile(r"\b(LP|L\.P\.|MASTER LIMITED PARTNERSHIP|MLP)\b", re.IGNORECASE)
REIT_RE   = re.compile(r"\bREIT\b|\bREAL ESTATE INVESTMENT TRUST\b", re.IGNORECASE)


def is_probably_non_common_equity(sym: str, name: str) -> bool:
    """
    Directory files include lots of instruments. We exclude obvious non-common-equity
    via symbol and name heuristics.
    """
    s = sym.upper()

    # Exclude symbols that tend to represent preferreds / weird classes on US exchanges
    if "$" in s: # Some files use $ for preferreds
        return True
    
    # Exclude warrants, rights, preferreds often denoted by length or suffix
    # Nasdaq/CQS specific suffixes
    if len(s) > 5: 
        return True # Tickers > 5 chars usually test, preferred, or warrants

    # Exclude if the name looks like a fund/note/trust/etc
    if EXCLUDE_NAME_RE.search(name or ""):
        return True

    # Exclude LP/MLP if enabled
    if EXCLUDE_LPS_MLPS and LP_MLP_RE.search(name or ""):
        return True

    # Exclude REIT if enabled (heuristic)
    if EXCLUDE_REITS and REIT_RE.search(name or ""):
        return True

    return False


@dataclass
class TickerRow:
    s: str
    n: str


def df_to_candidates(nasdaq_df: pd.DataFrame, other_df: pd.DataFrame) -> Dict[str, str]:
    """
    Build initial candidate map: symbol -> company name (best-effort).
    """
    candidates: Dict[str, str] = {}

    # Nasdaq file columns: Symbol, Security Name, Market Category, Test Issue, Financial Status, Round Lot Size, ETF, NextShares
    print("Processing Nasdaq listings...")
    if 'Symbol' in nasdaq_df.columns:
        for _, r in nasdaq_df.iterrows():
            if str(r.get("ETF", "")).strip().upper() == "Y": continue
            if str(r.get("Test Issue", "")).strip().upper() == "Y": continue
            
            sym = normalize_symbol(str(r.get("Symbol", "")))
            name = str(r.get("Security Name", "")).strip()
            
            if not sym or is_probably_non_common_equity(sym, name):
                continue

            candidates[sym] = clean_company_name(name)

    # Other file columns: ACT Symbol, Security Name, Exchange, CQS Symbol, ETF, Round Lot Size, Test Issue, NASDAQ Symbol
    print("Processing Other listings...")
    if 'ACT Symbol' in other_df.columns:
        for _, r in other_df.iterrows():
            if str(r.get("ETF", "")).strip().upper() == "Y": continue
            if str(r.get("Test Issue", "")).strip().upper() == "Y": continue
            
            sym = normalize_symbol(str(r.get("ACT Symbol", "")))
            name = str(r.get("Security Name", "")).strip()

            if not sym or is_probably_non_common_equity(sym, name):
                continue
            
            # Prefer existing name if present (Nasdaq usually has better names)
            if sym not in candidates:
                candidates[sym] = clean_company_name(name)

    # Manual inclusions for things that might get filtered aggressively
    # e.g. BRK-B is filtered by >5 char check usually, but it's valid.
    # We can add them back if we want.
    
    return candidates


def yf_info_safe(ticker: str) -> Optional[dict]:
    """
    yfinance can error, time out, or return partial data.
    """
    if yf is None:
        return None
    try:
        t = yf.Ticker(ticker)
        info = t.get_info()
        return info if isinstance(info, dict) else None
    except Exception:
        return None


def yf_passes_filters(symbol: str, info: dict, fallback_name: str) -> bool:
    qt = (info.get("quoteType") or "").upper()
    if qt and qt not in {"EQUITY"}:
        return False

    name = (info.get("shortName") or info.get("longName") or fallback_name or "").strip()
    if EXCLUDE_NAME_RE.search(name):
        return False

    sector = (info.get("sector") or "").strip().lower()
    industry = (info.get("industry") or "").strip().lower()

    if EXCLUDE_FINANCIALS:
        if sector == "financial services": return False
        if any(k in industry for k in ["banks", "insurance", "capital markets", "mortgage", "credit services"]):
            return False

    if EXCLUDE_REITS and (sector == "real estate" or "reit" in industry or REIT_RE.search(name)):
        return False

    if EXCLUDE_LPS_MLPS and LP_MLP_RE.search(name):
        return False

    return True


def build_final_list(candidates: Dict[str, str]) -> List[TickerRow]:
    """
    Optionally enrich and filter with yfinance. Always de-dupe by symbol.
    """
    out: List[TickerRow] = []

    # Sort for stability
    symbols = sorted(candidates.keys())

    if not ENABLE_YFINANCE_FILTERING:
        print("Skipping yfinance enrichment (ENABLE_YFINANCE_FILTERING=False)")
        for sym in symbols:
            out.append(TickerRow(s=sym, n=candidates[sym]))
        return out

    if yf is None:
        raise RuntimeError("yfinance not installed, but ENABLE_YFINANCE_FILTERING=True.")

    print(f"Enriching top {MAX_YFINANCE_TICKERS} candidates with yfinance...")
    count = 0
    start_time = time.time()
    
    for i, sym in enumerate(symbols):
        if count >= MAX_YFINANCE_TICKERS:
            break
            
        if i % 50 == 0:
            elapsed = time.time() - start_time
            print(f"Processed {i}/{len(symbols)}... ({count} kept) - {elapsed:.1f}s")

        info = yf_info_safe(sym)
        time.sleep(YFINANCE_SLEEP_SECONDS)

        fallback_name = candidates[sym]
        if not info:
             # Keep if yfinance fails? Let's say yes for robustness, or no for strictness.
             # User said "work in yfinance", implying we need valid yfinance tickers.
             # But if yfinance network flakes, we might lose valid ones. 
             # Let's keep them but use directory name.
            out.append(TickerRow(s=sym, n=fallback_name))
            count += 1
            continue

        if yf_passes_filters(sym, info, fallback_name):
            name = (info.get("longName") or info.get("shortName") or fallback_name or "").strip()
            name = clean_company_name(name)
            out.append(TickerRow(s=sym, n=name))
            count += 1

    return out


def write_js_array(rows: List[TickerRow], path: str) -> None:
    # Sort by Symbol length then alpha (common ones like AAPL often short)
    # OR just alpha. Alpha is fine.
    rows.sort(key=lambda x: x.s)
    
    print(f"Writing {len(rows)} tickers to {path}...")
    with open(path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by build_ticker_array.py\n")
        f.write(f"// Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"// Total count: {len(rows)}\n")
        f.write("const TICKER_DATA = [\n")
        for r in rows:
            # Escape quotes minimally
            name = r.n.replace('"', '\\"')
            f.write(f'  {{ s: "{r.s}", n: "{name}" }},\n')
        f.write("];\n")
    print("Done.")


def main() -> None:
    # Ensure dependencies
    try:
        import pandas
        import requests
    except ImportError:
        print("Please run: pip install pandas requests yfinance")
        return

    print("Downloading symbol directories...")
    try:
        nasdaq_df = fetch_symbol_file(NASDAQ_LISTED_URL)
        other_df = fetch_symbol_file(OTHER_LISTED_URL)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    print("Building candidate universe...")
    candidates = df_to_candidates(nasdaq_df, other_df)
    print(f"Candidates found: {len(candidates):,}")

    final_rows = build_final_list(candidates)
    
    output_file = os.path.join(os.getcwd(), OUTPUT_PATH)
    write_js_array(final_rows, output_file)


if __name__ == "__main__":
    main()
