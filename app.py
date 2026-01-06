from flask import Flask, render_template, request, jsonify
from dcf_loader import load_data_from_api
from dcf_code import DCFModel, DCFAssumptions
import os
import re
import math
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# =============================================================================
# SECURITY: Input Validation
# =============================================================================
TICKER_REGEX = re.compile(r'^[A-Z]{1,5}$')

def validate_ticker(ticker: str) -> str:
    """Validate ticker: 1-5 uppercase letters only"""
    if not ticker:
        raise ValueError("Ticker symbol is required")
    ticker = ticker.strip().upper()
    if not TICKER_REGEX.match(ticker):
        raise ValueError(f"Invalid ticker format: {ticker}. Must be 1-5 letters.")
    return ticker

def validate_growth_rate(val, min_val=-0.5, max_val=1.0, default=0.0) -> float:
    """Validate numeric input: reject NaN/Inf, clamp to bounds"""
    try:
        val = float(val)
        if math.isnan(val) or math.isinf(val):
            return default
        return max(min_val, min(max_val, val))
    except (TypeError, ValueError):
        return default

# =============================================================================
# SECURITY: Headers Middleware
# =============================================================================
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    # CSP: Allow Tailwind CDN, inline styles (required by Tailwind)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none';"
    )
    return response

# =============================================================================
# RATE LIMITING: Valuation Endpoint
# =============================================================================
_valuation_rate_limit = {}
VALUATION_RATE_WINDOW = 60  # seconds
VALUATION_RATE_MAX = 10     # max valuations per minute per IP

def check_valuation_rate_limit(ip: str) -> bool:
    """Returns True if request is allowed, False if rate limited"""
    now = time.time()
    if ip not in _valuation_rate_limit:
        _valuation_rate_limit[ip] = []
    _valuation_rate_limit[ip] = [t for t in _valuation_rate_limit[ip] if now - t < VALUATION_RATE_WINDOW]
    if len(_valuation_rate_limit[ip]) >= VALUATION_RATE_MAX:
        return False
    _valuation_rate_limit[ip].append(now)
    return True

# =============================================================================
# ROUTES
# =============================================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Rate limiting for expensive valuation endpoint
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if not check_valuation_rate_limit(client_ip):
            return render_template('index.html', error="Rate limit exceeded. Please wait 1 minute before submitting again.")
        
        try:
            # 1. Validate Inputs
            ticker = validate_ticker(request.form.get('ticker', ''))
            
            g_rates = [
                validate_growth_rate(request.form.get(f'g{i}', 0.0), min_val=-0.5, max_val=1.0)
                for i in range(1, 6)
            ]
            term_g = validate_growth_rate(request.form.get('term_g', 0.0), min_val=-0.1, max_val=0.15)
            
            # 2. Run Model (with timeout protection from loader)
            data = load_data_from_api(ticker)
            assumptions = DCFAssumptions(
                revenue_growth_rates=g_rates,
                terminal_growth_rate=term_g
            )
            model = DCFModel(data, assumptions)
            val = model.calculate_intrinsic_value()
            
            # 3. Sensitivity & Heatmap Logic
            g_steps, matrix = model.generate_sensitivity_table()
            
            all_prices = [p for _, row in matrix for p in row]
            min_p, max_p = min(all_prices), max(all_prices)
            current_p = data.stock_price
            
            sensitivity_data = {
                "headers": ["WACC"] + [f"{g:.1%}" for g in g_steps],
                "rows": []
            }
            
            for wacc, prices in matrix:
                row_items = [{"value": f"{wacc:.1%}", "style": "font-weight: bold; background-color: #f3f4f6;"}]
                
                for p in prices:
                    if p >= current_p:
                        denom = max_p - current_p
                        intensity = (p - current_p) / denom if denom > 0 else 0
                        alpha = 0.1 + (0.6 * intensity)
                        bg_color = f"rgba(34, 197, 94, {alpha:.2f})"
                    else:
                        denom = current_p - min_p
                        intensity = (current_p - p) / denom if denom > 0 else 0
                        alpha = 0.1 + (0.6 * intensity)
                        bg_color = f"rgba(239, 68, 68, {alpha:.2f})"
                        
                    row_items.append({
                        "value": f"${p:,.2f}", 
                        "style": f"background-color: {bg_color};"
                    })
                    
                sensitivity_data["rows"].append(row_items)

            return render_template(
                'result.html',
                ticker=ticker,
                price=data.stock_price,
                value=val,
                wacc=model.wacc,
                projections=model.projections,
                sensitivity=sensitivity_data,
                calculation_log=model.calculation_log
            )
            
        except ValueError as e:
            # User input errors - safe to display
            return render_template('index.html', error=str(e))
        except Exception as e:
            # Internal errors - log full, show generic
            logger.error(f"DCF Calculation Error: {e}", exc_info=True)
            return render_template('index.html', error="An error occurred processing your request. Please check the ticker symbol and try again.")
            
    return render_template('index.html')

# Production: debug is controlled by environment variable
if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode)

