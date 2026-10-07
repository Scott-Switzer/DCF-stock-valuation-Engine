# Valuation submissions as research data

D1 `valuations` contains private submissions, not trades or observed beliefs of a representative market sample. Inputs, source provenance and forecast assumptions are retained so unrealistic assumptions and coverage gaps can be examined. `model_version` separates methodologies as the suite expands. `is_demo=1` must always be excluded from real-company research.

An owner-only exploratory query:

```sql
SELECT ticker, substr(created_at,1,10) AS submission_day, method, model_version,
       count(*) AS scenarios,
       count(DISTINCT client_hash) AS daily_network_hashes,
       avg(json_extract(result_json,'$.upside_12m')) AS mean_assumed_12m_upside,
       min(json_extract(result_json,'$.upside_12m')) AS minimum_assumed_12m_upside,
       max(json_extract(result_json,'$.upside_12m')) AS maximum_assumed_12m_upside
FROM valuations
WHERE is_demo=0
GROUP BY ticker, submission_day, method, model_version
HAVING count(DISTINCT client_hash)>=5;
```

These network hashes are not person IDs: NAT can combine people, and the daily salt input changes across days. Distinct assumptions by one network are multiple scenarios. Do not equate scenario counts with votes. Examine price dates, valuation dates, source quality, assumption extremes and model versions before aggregation. Prefer robust medians/quantiles and show sample size and selection bias if publishing a future dashboard; no public aggregate endpoint is enabled yet. Bots and intentional manipulation remain possible despite rate limits and deduplication.

Database queries and exports require authenticated Cloudflare access. Do not publish individual records or the daily network hashes. Research retention and owner-assisted deletion are described in the public privacy notice.
