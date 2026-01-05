
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from dcf_loader import load_data_from_api
from dcf_code import DCFModel, DCFAssumptions

st.set_page_config(page_title="DCF Valuation Model", layout="wide")

st.title("Discounted Cash Flow (DCF) Valuation")
st.markdown("### Hybrid Data Pipeline: Edgar + YFinance")

# --- Sidebar Inputs ---
st.sidebar.header("Model Inputs")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL").upper()
terminal_growth = st.sidebar.slider("Terminal Growth Rate", 0.01, 0.05, 0.025, 0.005)

st.sidebar.subheader("Revenue Growth Rates (Next 5 Years)")
g1 = st.sidebar.number_input("Year 1 Growth", value=0.05)
g2 = st.sidebar.number_input("Year 2 Growth", value=0.05)
g3 = st.sidebar.number_input("Year 3 Growth", value=0.04)
g4 = st.sidebar.number_input("Year 4 Growth", value=0.04)
g5 = st.sidebar.number_input("Year 5 Growth", value=0.03)

run_model = st.sidebar.button("Calculate Valuation")

if run_model:
    with st.spinner(f"Fetching data for {ticker}..."):
        try:
            # 1. Load Data
            data = load_data_from_api(ticker)
            
            # 2. Setup Model
            assumptions = DCFAssumptions(
                revenue_growth_rates=[g1, g2, g3, g4, g5],
                terminal_growth_rate=terminal_growth
            )
            model = DCFModel(data, assumptions)
            
            # 3. Validation
            val = model.calculate_intrinsic_value() # Runs logic, prints to console (hidden from web user)
            
            # --- Results Display ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"${data.stock_price:,.2f}")
            col2.metric("Intrinsic Value", f"${val:,.2f}", delta=f"{((val/data.stock_price)-1):.1%}")
            col3.metric("WACC", f"{model.wacc:.2%}")
            
            # --- Projections Data ---
            st.subheader("Financial Projections")
            proj_df = pd.DataFrame(model.projections)
            st.dataframe(proj_df.set_index("Year").style.format("{:,.0f}"))
            
            # --- Sensitivity Analysis ---
            st.subheader("Sensitivity Analysis: WACC vs Terminal Growth")
            
            g_steps, matrix = model.generate_sensitivity_table()
            
            # Convert to DataFrame for Heatmap
            wacc_labels = [f"{w:.2%}" for w, _ in matrix]
            growth_labels = [f"{g:.2%}" for g in g_steps]
            
            prices = [row[1] for row in matrix] # Extract just the prices lists
            
            sens_df = pd.DataFrame(prices, index=wacc_labels, columns=growth_labels)
            
            # Plot
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(sens_df, annot=True, fmt=".2f", cmap="RdYlGn", center=data.stock_price, ax=ax)
            ax.set_title("Intrinsic Value Sensitivity Matrix")
            ax.set_ylabel("WACC")
            ax.set_xlabel("Terminal Growth Rate")
            
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Error running model: {e}")
