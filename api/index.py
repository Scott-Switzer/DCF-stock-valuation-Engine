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
            
            # 3. Sensitivity & Heatmap Logic
            g_steps, matrix = model.generate_sensitivity_table()
            
            # Find range for color scaling
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
                    # Color Logic: Relative to Current Price
                    if p >= current_p:
                        # Green Intensity
                        # Scale: (p - curr) / (max - curr) -> 0 to 1
                        intensity = (p - current_p) / (max_p - current_p) if max_p > current_p else 0
                        alpha = 0.1 + (0.6 * intensity) # Min 0.1, Max 0.7 opacity
                        bg_color = f"rgba(34, 197, 94, {alpha:.2f})" # Tailwind Green-500
                    else:
                        # Red Intensity
                        # Scale: (curr - p) / (curr - min) -> 0 to 1
                        intensity = (current_p - p) / (current_p - min_p) if current_p > min_p else 0
                        alpha = 0.1 + (0.6 * intensity)
                        bg_color = f"rgba(239, 68, 68, {alpha:.2f})" # Tailwind Red-500
                        
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
                sensitivity=sensitivity_data
            )
            
        except Exception as e:
            return render_template('index.html', error=str(e))
            
    return render_template('index.html')

# Vercel requires the app to be exposed as 'app'
if __name__ == '__main__':
    app.run(debug=True)
