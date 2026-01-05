from dcf_code import DCFModel, DCFAssumptions
from dcf_loader import load_data_from_api 

# 1. Load Data (REAL API)
try:
    # 1. Get Ticker
    ticker = input("\nEnter Ticker Symbol (default: AAPL): ").strip().upper()
    if not ticker:
        ticker = "AAPL"
        
    data = load_data_from_api(ticker)
    
    # 2. Define Assumptions (Interactive Input)
    print("\n--- ENTER FORECAST ASSUMPTIONS ---")
    growth_rates = []
    print("Please enter revenue growth rates for the next 5 years (e.g., 0.05 for 5%):")
    for i in range(1, 6):
        while True:
            try:
                rate = float(input(f"   Year {i} Growth Rate: "))
                growth_rates.append(rate)
                break
            except ValueError:
                print("   Invalid input. Please enter a decimal (e.g. 0.05)")

    while True:
        try:
            term_growth = float(input("   Terminal Growth Rate (e.g. 0.025): "))
            break
        except ValueError:
            print("   Invalid input. Please enter a decimal.")

    assumptions = DCFAssumptions(
        revenue_growth_rates=growth_rates,
        terminal_growth_rate=term_growth,
        projection_years=5
    )

    # 3. Run Model
    print("\n--- Running DCF Model (Live Data) ---")
    model = DCFModel(data, assumptions)
    value = model.calculate_intrinsic_value()

    print(f"\nCalculated Target Price: ${value}")
    
    # --- Sensitivity Analysis ---
    from tabulate import tabulate
    
    print("\n" + "="*60)
    print(" SENSITIVITY ANALYSIS (Target Price)")
    print("="*60)
    print("Rows: WACC | Cols: Terminal Growth Rate")
    
    g_steps, matrix = model.generate_sensitivity_table()
    
    # Format Headers (Growth Rates)
    headers = ["WACC / Growth"] + [f"{g:.1%}" for g in g_steps]
    
    # Format Rows
    table_data = []
    for wacc, prices in matrix:
        # Highlight approximate base case in future if needed
        row_label = f"{wacc:.1%}"
        formatted_prices = [f"${p:,.2f}" for p in prices]
        table_data.append([row_label] + formatted_prices)
        
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
except Exception as e:
    print(f"\n❌ Execution Failed: {e}")
