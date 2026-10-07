from guidance import filing_links, guidance_excerpt


def test_filings_are_issuer_bound_dated_and_earnings_related():
    packet = {
        "cik": 320193,
        "filings": {
            "recent": {
                "form": ["8-K", "8-K", "10-Q"],
                "items": ["5.02", "2.02,9.01", ""],
                "accessionNumber": [
                    "0000320193-26-000001",
                    "0000320193-26-000002",
                    "0000320193-26-000003",
                ],
                "primaryDocument": ["one.htm", "two.htm", "three.htm"],
                "filingDate": ["2026-08-01", "2026-07-30", "2026-07-31"],
                "reportDate": ["2026-08-01", "2026-06-30", "2026-06-30"],
            }
        },
    }
    rows = filing_links(packet, 320193, "2026-08-02")
    assert len(rows) == 2
    assert rows[0]["form"] == "8-K"
    assert "/320193/000032019326000002/" in rows[0]["url"]
    assert all(x["filed"] <= "2026-08-02" for x in rows)
    assert filing_links(packet, 123, "2026-08-02") == []


def test_guidance_excerpt_requires_forward_period_and_metric():
    assert guidance_excerpt("<p>Revenue increased 12% last quarter.</p>") is None
    assert (
        guidance_excerpt(
            "<p>Forward-looking statements involve risks. We expect markets to change.</p>"
        )
        is None
    )
    text = "For the next quarter, we expect revenue between $10 and $12 billion."
    assert guidance_excerpt("<p>" + text + "</p>") == text


def test_customer_expectations_and_safe_harbor_are_not_management_guidance():
    assert guidance_excerpt('<p>Customers expect sales to decline next fiscal year as spending changes.</p>') is None
    assert guidance_excerpt('<p>Our forward-looking statements include revenue we expect next quarter, subject to risks and uncertainties.</p>') is None
