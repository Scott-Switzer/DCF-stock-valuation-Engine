"""Refresh local autocomplete from Nasdaq symbol directories using public metadata."""

import csv
import io
import json
from pathlib import Path
import re
import requests

URLS = [
    "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
    "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
]
EXCLUDE = re.compile(r"\b(ETF|ETN|FUND|REIT|WARRANT|RIGHTS|PREFERRED|MLP|LP)\b", re.I)


def generate():
    entries = {}
    for url in URLS:
        response = requests.get(url, timeout=(3, 15))
        response.raise_for_status()
        for row in csv.DictReader(io.StringIO(response.text), delimiter="|"):
            if row.get("Test Issue") == "Y" or row.get("ETF") == "Y":
                continue
            symbol = (row.get("Symbol") or row.get("ACT Symbol") or "").replace(".", "-")
            name = row.get("Security Name", "")
            if not re.fullmatch(r"[A-Z]{1,6}(?:-[A-Z]{1,2})?", symbol) or EXCLUDE.search(name):
                continue
            entries[symbol] = {"s": symbol, "n": name}
    if not entries:
        raise RuntimeError("Ticker source returned no symbols; existing list preserved.")
    raw = json.dumps([entries[k] for k in sorted(entries)], ensure_ascii=False, indent=2)
    target = Path(__file__).parent / "static/js/tickers.js"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(
        "// Public symbol metadata. Eligibility must be verified before valuation.\nconst TICKER_DATA = "
        + raw
        + ";\n"
    )
    tmp.replace(target)


if __name__ == "__main__":
    generate()
