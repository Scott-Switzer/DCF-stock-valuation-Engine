"""Optional issuer-bound SEC research. Guidance prose is never a forecast input."""

from datetime import date, datetime, timezone
from html.parser import HTMLParser
import re
from urllib.parse import quote
from dcf_loader import JsonHTTP, ProviderError, provider_setting, ticker_symbol


def filing_links(packet, cik, asof):
    if str(packet.get("cik", "")).lstrip("0") != str(cik).lstrip("0"):
        return []
    recent = packet.get("filings", {}).get("recent", {})
    rows = []
    counts = {}
    for i, form in enumerate(recent.get("form", [])):
        try:
            filed = recent["filingDate"][i]
            if date.fromisoformat(filed) > date.fromisoformat(asof):
                continue
            if form not in {"8-K", "10-Q", "10-K"} or counts.get(form, 0) >= 1:
                continue
            if form == "8-K" and "2.02" not in recent.get("items", [])[i]:
                continue
            accession = recent["accessionNumber"][i]
            primary = recent["primaryDocument"][i]
            if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession) or not re.fullmatch(
                r"[A-Za-z0-9_.-]+", primary
            ):
                continue
            base = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/"
            )
            rows.append(
                {
                    "form": form,
                    "filed": filed,
                    "report_date": recent["reportDate"][i],
                    "url": base + quote(primary),
                    "directory": base,
                    "accession": accession,
                }
            )
            counts[form] = counts.get(form, 0) + 1
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return rows


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        if tag in {"p", "div", "tr", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        if tag in {"p", "div", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def forward_period(text, filed, expectation_position):
    periods = list(re.finditer(
        r"\b(next|coming)\s+(quarter|fiscal year|year)\b|\b(fiscal(?:\s+year)?|full.year|first quarter|second quarter|third quarter|fourth quarter|Q[1-4])\s*(20\d{2})\b",
        text, re.I,
    ))
    if not periods:
        return False
    period = min(periods, key=lambda match: min(
        abs(match.start() - expectation_position), abs(match.end() - expectation_position)
    ))
    if period.group(1):
        return True
    year = int(period.group(4))
    if year < filed.year:
        return False
    # Fiscal-quarter boundaries are unknown: only an unambiguously future year qualifies.
    if re.search(r"quarter|Q[1-4]", period.group(3), re.I):
        return year > filed.year
    return True


def guidance_excerpt(html, filed=None):
    filed = date.fromisoformat(filed) if filed else datetime.now(timezone.utc).date()
    parser = Paragraphs()
    parser.feed(html[:1_500_000])
    for paragraph in "".join(parser.parts).split("\n"):
        text = " ".join(paragraph.split())
        expectation = re.search(
            r"\b(we|our company|the company)\s+(expect|expects|anticipate|anticipates|project|projects)\b",
            text, re.I,
        )
        if (
            40 <= len(text) <= 700
            and re.search(r"\b(revenue|sales)\b", text, re.I)
            and expectation
            and forward_period(text, filed, expectation.start())
            and not re.search(r"forward.looking|safe.harbor|risks and uncertainties", text, re.I)
        ):
            return text
    return None


def load_guidance(ticker):
    ticker = ticker_symbol(ticker)
    identity = provider_setting("EDGAR_IDENTITY")
    if "@" not in identity:
        raise ProviderError("SEC research is not configured.")
    http = JsonHTTP(budget=8)
    headers = {"User-Agent": identity, "Accept": "application/json"}
    directory = http.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers,
        ttl=21600,
        cache_key="sec-directory",
    )
    issuer = next(
        (
            x
            for x in directory.values()
            if isinstance(x, dict) and str(x.get("ticker", "")).replace(".", "-") == ticker
        ),
        None,
    )
    if not issuer:
        raise ProviderError("No SEC issuer match for this ticker.")
    cik = issuer["cik_str"]
    packet = http.get(
        f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",
        headers=headers,
        ttl=21600,
        cache_key=f"sec-classification-{int(cik):010d}",
    )
    now = datetime.now(timezone.utc)
    rows = filing_links(packet, cik, now.date().isoformat())
    for row in rows:
        if row["form"] != "8-K" or (now.date() - date.fromisoformat(row["filed"])).days > 180:
            continue
        try:
            index = http.get(
                row["directory"] + "index.json",
                headers=headers,
                ttl=86400,
                cache_key="sec-guidance-index-" + row["accession"],
            )
            files = index.get("directory", {}).get("item", [])
            candidates = [
                x["name"]
                for x in files
                if isinstance(x, dict)
                and re.fullmatch(r"[A-Za-z0-9_.-]+\.html?", x.get("name", ""))
                and re.search(r"(99.?1|ex.?99|earnings|press)", x["name"], re.I)
            ][:2]
            for name in candidates:
                url = row["directory"] + quote(name)
                html = http.get(
                    url,
                    headers={"User-Agent": identity, "Accept": "text/html"},
                    ttl=86400,
                    cache_key="sec-guidance-text-" + row["accession"] + "-" + name,
                    text_response=True,
                )
                excerpt = guidance_excerpt(html, row["filed"])
                if excerpt:
                    row.update(excerpt=excerpt, url=url)
                    break
        except (ProviderError, ValueError, TypeError):
            pass
    has_guidance = any(x.get("excerpt") for x in rows)
    return {
        "ticker": ticker,
        "issuer": packet.get("name"),
        "retrieved_at": now.isoformat(),
        "filings": rows,
        "note": "Revenue outlook excerpt from the issuer’s earnings filing. Confirm management attribution and review the linked source and forecast period before changing assumptions."
        if has_guidance
        else "No clear management revenue outlook was extracted. Open the latest earnings filing or periodic report to review management commentary; these links do not imply guidance was provided.",
    }
