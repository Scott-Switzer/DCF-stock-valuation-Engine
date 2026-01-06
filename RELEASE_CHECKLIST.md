# Release Readiness Checklist

## Pre-Release Verification (30 min)

### 1. Security Checks ✓
```bash
# Run locally before deploy
python3 -c "from app import validate_ticker; validate_ticker('AAPL')"  # Should pass
python3 -c "from app import validate_ticker; validate_ticker('INVALID123')"  # Should raise
```
**Expected**: Valid ticker passes, invalid raises `ValueError`

### 2. Input Validation
```bash
curl -X POST http://localhost:5000/ -d "ticker=<script>alert(1)</script>"
```
**Expected**: Error message "Invalid ticker format", no XSS execution

### 3. Security Headers
```bash
curl -I http://localhost:5000/
```
**Expected output includes**:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'...
```

### 4. Rate Limiting
```bash
for i in {1..15}; do curl -X POST localhost:5000/ -d "ticker=AAPL&g1=0.05&g2=0.05&g3=0.04&g4=0.04&g5=0.03&term_g=0.02" -o /dev/null -s -w "%{http_code}\n"; done
```
**Expected**: First 10 return 200, then "Rate limit exceeded" error

### 5. Smoke Test - Full Valuation
1. Go to https://dcf-stock-valuation-engine.onrender.com/
2. Enter: AAPL, growth rates: 0.05, 0.05, 0.04, 0.04, 0.03, terminal: 0.02
3. **Expected**: Valuation result page with price, intrinsic value, sensitivity table

### 6. Edge Cases
| Test | Input | Expected |
|------|-------|----------|
| Empty ticker | `` | "Ticker symbol is required" |
| Too long | `ABCDEFGH` | "Invalid ticker format" |
| Numbers | `AAPL123` | "Invalid ticker format" |
| NaN growth | `NaN` | Treated as 0.0 |
| Huge growth | `999` | Clamped to 1.0 (100%) |
| Negative growth | `-0.9` | Clamped to -0.5 |

---

## Rollback Plan

### Immediate Rollback (< 2 min)
```bash
git revert HEAD --no-edit
git push origin main
```
Render auto-deploys on push.

### Manual Rollback on Render
1. Dashboard → dcf-stock-valuation-engine
2. Deploys → Select previous working deploy
3. Click "Rollback to this deploy"

---

## What Changed

| File | Changes |
|------|---------|
| `app.py` | +Input validation, +Security headers, +Rate limiting |
| `dcf_loader.py` | +HTTP timeouts, +Retry logic, +Session pooling |
| `requirements.txt` | Pinned all versions |
| `Dockerfile` | Gunicorn: 4 workers × 4 threads, 30s timeout |

## Post-Deploy Monitoring
- Check Render logs for 5xx errors
- Monitor response times (should be < 8s for valuation)
- Watch for rate limit 429s (indicates abuse protection working)
