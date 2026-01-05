from flask import Flask, render_template, request
from dcf_loader import load_data_from_api
from dcf_code import DCFModel, DCFAssumptions
import pandas as pd
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # 1. Get Inputs
            ticker = request.form.get('ticker', 'AAPL').upper()
            g_rates = [
                float(request.form.get(f'g{i}', 0.05)) 
                for i in range(1, 6)
            ]
            term_g = float(request.form.get('term_g', 0.025))
            
            # 2. Run Model
            data = load_data_from_api(ticker)
            assumptions = DCFAssumptions(
                revenue_growth_rates=g_rates,
                terminal_growth_rate=term_g
            )
            model = DCFModel(data, assumptions)
            val = model.calculate_intrinsic_value()
            
            # 3. Sensitivity
            g_steps, matrix = model.generate_sensitivity_table()
            
            # Format Data for Template
            sensitivity_data = {
                "headers": ["WACC"] + [f"{g:.1%}" for g in g_steps],
                "rows": []
            }
            for wacc, prices in matrix:
                row = [f"{wacc:.1%}"] + [f"${p:,.2f}" for p in prices]
                sensitivity_data["rows"].append(row)

            return render_template(
                'result.html',
                ticker=ticker,
                price=data.stock_price,
                value=val,
                wacc=model.wacc,
                projections=model.projections,
                sensitivity=sensitivity_data
            )
            
        except Exception as e:
            return render_template('index.html', error=str(e))
            
    return render_template('index.html')

# Vercel requires the app to be exposed as 'app'
if __name__ == '__main__':
    app.run(debug=True)
