import os
from flask import Flask, render_template, request, jsonify
from dcf_code import DCFModel, DCFAssumptions
from dcf_loader import load_data_from_api
import traceback
import sys
from io import StringIO

app = Flask(__name__)

# API key must be set as environment variable
# No default API key for security

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate_dcf():
    """
    API endpoint to calculate DCF valuation
    Expects JSON: {
        "ticker": "AAPL",
        "growth_rates": [0.05, 0.05, 0.04, 0.04, 0.03],
        "terminal_growth": 0.025
    }
    """
    try:
        data = request.get_json()
        
        # Validate inputs
        ticker = data.get('ticker', '').strip().upper()
        if not ticker:
            return jsonify({'error': 'Ticker symbol is required'}), 400
        
        growth_rates = data.get('growth_rates', [])
        if len(growth_rates) != 5:
            return jsonify({'error': 'Exactly 5 growth rates required'}), 400
        
        terminal_growth = data.get('terminal_growth')
        if terminal_growth is None:
            return jsonify({'error': 'Terminal growth rate is required'}), 400
        
        # Capture console output for transparency
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Load financial data
            financial_data = load_data_from_api(ticker)
            
            # Create assumptions
            assumptions = DCFAssumptions(
                revenue_growth_rates=growth_rates,
                terminal_growth_rate=terminal_growth,
                projection_years=5
            )
            
            # Run DCF model
            model = DCFModel(financial_data, assumptions)
            target_price = model.calculate_intrinsic_value()
            
            # Get calculation logs
            calculation_logs = captured_output.getvalue()
            
        finally:
            sys.stdout = old_stdout
        
        # Prepare response with key data
        response = {
            'success': True,
            'target_price': target_price,
            'current_price': financial_data.stock_price,
            'ticker': ticker,
            'wacc': round(model.wacc * 100, 2),
            'projections': model.projections,
            'calculation_logs': calculation_logs,
            'company_data': {
                'market_cap': financial_data.market_cap,
                'beta': financial_data.beta,
                'shares_outstanding': financial_data.shares_outstanding,
                'total_debt': financial_data.total_debt[-1] if financial_data.total_debt else 0,
                'cash': financial_data.cash_and_equivalents[-1] if financial_data.cash_and_equivalents else 0
            }
        }
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Calculation failed: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Use environment variable for port (required for Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
