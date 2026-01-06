from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class DCFAssumptions:
    """
    Container for USER inputs: only growth rates and terminal parameters.
    Everything else is fetched from API.
    """
    revenue_growth_rates: List[float]  # e.g., [0.05, 0.04, 0.04, 0.03, 0.03]
    terminal_growth_rate: float        # e.g., 0.02
    projection_years: int = 5


@dataclass
class FinancialData:
    """
    Container for all data fetched from the API (Company financials + Market data).
    Stores LISTS of floats for historical data (e.g., last 3 years).
    Order: [Year n-2, Year n-1, Year n (most recent)]
    """
    # Income Statement (Historical)
    years: List[str]          # ['2021', '2022', '2023']
    revenue: List[float]
    ebit: List[float]
    ebitda: List[float]
    net_income: List[float]
    effective_tax_rate: List[float]
    interest_expense: List[float]

    # Balance Sheet (Historical)
    current_assets: List[float]
    current_liabilities: List[float]
    cash_and_equivalents: List[float]
    short_term_debt: List[float]
    long_term_debt: List[float]
    total_debt: List[float]
    total_assets: List[float]
    total_liabilities: List[float]
    property_plant_equipment_net: List[float] # Needed for derived CapEx
    preferred_equity: List[float]             # Needed for WACC
    
    # Cash Flow (Historical)
    d_and_a: List[float]
    capex: List[float]
    preferred_dividends: List[float]          # Needed for Cost of Preferred


    
    # Market / Profile Data
    shares_outstanding: float
    beta: float
    stock_price: float
    market_cap: float
    
    # Market assumptions fetched/defined programmatically (not user input)
    risk_free_rate: float
    market_return_rate: float    

    @property
    def nwc(self) -> List[float]:
        # Calculate NWC for each year in history
        # (CA - Cash) - (CL - Short Term Debt)
        nwc_list = []
        for i in range(len(self.current_assets)):
            op_assets = self.current_assets[i] - self.cash_and_equivalents[i]
            op_liabs = self.current_liabilities[i] - self.short_term_debt[i]
            nwc_list.append(op_assets - op_liabs)
        return nwc_list

    @property
    def book_value(self) -> List[float]:
        # TA - TL for each year
        return [a - l for a, l in zip(self.total_assets, self.total_liabilities)]


import numpy as np
import io
import sys

class DCFModel:
    def __init__(self, data: FinancialData, assumptions: DCFAssumptions):
        self.data = data
        self.assumptions = assumptions
        self.wacc = 0.0
        self.projections = []
        self.calculation_log = []  # Stores output for web display
        
    def _log(self, message: str):
        """Print AND store message for web transparency"""
        print(message)
        self.calculation_log.append(message)
        
    def _print_header(self, title):
        self._log(f"\n{'='*60}")
        self._log(f" {title}")
        self._log(f"{'='*60}")

    def _calculate_historical_margins(self):
        """
        PHASE 1: THE HISTORICAL "DRIVERS"
        ---------------------------------
        Logic: The model looks backward to establish a baseline before looking forward.
        It calculates key operating percentages (Margins) from the last 3 years of data.
        """
        self._print_header("PHASE 1: HISTORICAL DRIVERS (BASELINE)")
        
        # Convert List[float] to numpy arrays for vector math
        rec_count = min(len(self.data.revenue), 3) # Strict 3-year window for averaging
        
        # Extract last 'rec_count' years (Order: Oldest -> Newest)
        rev = np.array(self.data.revenue[-rec_count:])
        ebit = np.array(self.data.ebit[-rec_count:])
        da = np.array(self.data.d_and_a[-rec_count:])
        
        # NWC List handling
        nwc_list = self.data.nwc
        nwc = np.array(nwc_list[-rec_count:])
        
        # CapEx Handling
        capex = np.array(self.data.capex[-rec_count:])

        # Print Historical Inputs
        def fmt_list(arr):
            return "[" + ", ".join([f"{x:,.0f}" for x in arr]) + "]"

        self._log(f"Years Used:           {self.data.years[-rec_count:]}")
        self._log(f"Historical Revenue:   {fmt_list(rev)}")
        self._log(f"Historical EBIT:      {fmt_list(ebit)}")
        self._log(f"Historical D&A:       {fmt_list(da)}")
        self._log(f"Historical CapEx:     {fmt_list(capex)}")
        self._log(f"Historical NWC:       {fmt_list(nwc)}")

        try:
            # 1. OPERATING MARGINS (ROWS 13-29)
            # EBIT Margin = EBIT / Revenue
            ebit_margins = ebit / rev
            avg_ebit_m = np.mean(ebit_margins)
            
            # D&A Margin = D&A / Revenue
            da_margins = da / rev
            avg_da_m = np.mean(da_margins)
            
            # NWC Margin = Net Working Capital / Revenue
            nwc_margins = nwc / rev
            avg_nwc_m = np.mean(nwc_margins)
            
            # CapEx Margin = CapEx / Revenue (Absolute value)
            capex_margins = np.abs(capex) / rev
            avg_capex_m = np.mean(capex_margins)
            
            self._log(f"\n--- Calculated Margins (Last 3 Years) ---")
            self._log(f"EBIT Margins:   {ebit_margins}")
            self._log(f"Avg EBIT Margin: {avg_ebit_m:.4%}")
            
            self._log(f"D&A Margins:    {da_margins}")
            self._log(f"Avg D&A Margin:  {avg_da_m:.4%}")
            
            self._log(f"NWC Margins:    {nwc_margins}")
            self._log(f"Avg NWC Margin:  {avg_nwc_m:.4%}")
            
            self._log(f"CapEx Margins:  {capex_margins}")
            self._log(f"Avg CapEx Margin:{avg_capex_m:.4%}")
            
        except ZeroDivisionError:
            print("Error: Zero Revenue found, cannot calculate margins.")
            return 0,0,0,0,0

        # Return averages + the most recent actual NWC balance (Year 0 baseline for Year 1 change)
        return avg_ebit_m, avg_da_m, avg_nwc_m, avg_capex_m, nwc[-1]

    def calculate_wacc(self) -> float:
        """
        PHASE 4 (Helper): DISCOUNT RATE (WACC)
        """
        self._print_header("CALCULATING WACC")
        
        # 1. Cost of Equity (CAPM)
        rf = self.data.risk_free_rate
        beta = self.data.beta
        rm = self.data.market_return_rate
        cost_equity = rf + beta * (rm - rf)
        
        self._log(f"1. Cost of Equity (CAPM)")
        self._log(f"   Risk Fee Rate: {rf:.2%}")
        self._log(f"   Beta:          {beta:.3f}")
        self._log(f"   Market Return: {rm:.2%}")
        self._log(f"   -> Cost Equity: {cost_equity:.2%}")

        # 2. Cost of Debt (After Tax)
        total_debt = self.data.total_debt[-1] if self.data.total_debt else 0
        int_exp = abs(self.data.interest_expense[-1]) if self.data.interest_expense else 0
        
        cost_of_debt = int_exp / total_debt if total_debt > 0 else 0.05 
        tax_rate = self.data.effective_tax_rate[-1] if self.data.effective_tax_rate else 0.21
        cost_debt_at = cost_of_debt * (1 - tax_rate)
        
        self._log(f"\n2. Cost of Debt")
        self._log(f"   Interest Exp:  ${int_exp:,.0f}")
        self._log(f"   Total Debt:    ${total_debt:,.0f}")
        self._log(f"   Pre-Tax Cost:  {cost_of_debt:.2%}")
        self._log(f"   Tax Rate:      {tax_rate:.2%}")
        self._log(f"   -> After-Tax:   {cost_debt_at:.2%}")

        # 3. Capital Structure Weights
        market_cap = self.data.market_cap
        pref_equity = self.data.preferred_equity[-1] if self.data.preferred_equity else 0
        
        total_value = market_cap + total_debt + pref_equity
        
        if total_value == 0:
            return 0.10
            
        w_equity = market_cap / total_value
        w_debt = total_debt / total_value
        w_pref = pref_equity / total_value
        
        # Cost of Preferred
        pref_divs = self.data.preferred_dividends[-1] if self.data.preferred_dividends else 0
        cost_pref = abs(pref_divs) / pref_equity if pref_equity > 0 else 0
        
        self._log(f"\n3. Weighting")
        self._log(f"   Market Cap:    ${market_cap:,.0f} ({w_equity:.1%})")
        self._log(f"   Total Debt:    ${total_debt:,.0f} ({w_debt:.1%})")
        self._log(f"   Pref Equity:   ${pref_equity:,.0f} ({w_pref:.1%})")
        
        wacc = (w_equity * cost_equity) + (w_debt * cost_debt_at) + (w_pref * cost_pref)
        self.wacc = wacc
        
        self._log(f"\n-> FINAL WACC: {wacc:.4%}")
        return wacc

    def forecast_cash_flows(self):
        """
        PHASE 2 & 3: PROJECTIONS & FREE CASH FLOW BUILD
        """
        # Retrieve Phase 1 Drivers
        ebit_m, da_m, nwc_m, capex_m, last_nwc = self._calculate_historical_margins()
        
        self._print_header("PHASE 2 & 3: PROJECTIONS & UFCF")
        self._log(f"Base Revenue: ${self.data.revenue[-1]:,.0f}")
        
        projections = []
        curr_rev = self.data.revenue[-1] # Base Revenue (Year 0)
        
        # NWC Anchor
        prev_nwc = last_nwc
        
        # Tax Rate used for projections
        tax_rate = self.data.effective_tax_rate[-1] if self.data.effective_tax_rate else 0.21
        
        self._log(f"{'Year':<5} | {'Revenue':<15} | {'EBIT':<15} | {'Taxes':<12} | {'NOPAT':<15} | {'D&A':<12} | {'CapEx':<12} | {'Chg NWC':<12} | {'UFCF':<15}")
        self._log("-" * 140)

        for i, g in enumerate(self.assumptions.revenue_growth_rates):
            # 1. Project Revenue
            curr_rev *= (1 + g)
            
            # 2. Derive Operating Line Items
            ebit = curr_rev * ebit_m
            taxes = ebit * tax_rate # Tax Expense
            nopat = ebit - taxes
            da = curr_rev * da_m
            capex = curr_rev * capex_m
            
            # 3. Calculate Change in NWC
            nwc_level = curr_rev * nwc_m
            change_nwc = nwc_level - prev_nwc
            
            # 4. UFCF Formula
            # UFCF = NOPAT + D&A - CapEx - Change NWC
            ufcf = nopat + da - capex - change_nwc
            
            if i == 0:
                 # Special logic check for Year 1 NWC change
                 pass 

            row = {
                "Year": i + 1,
                "Revenue": curr_rev,
                "EBIT": ebit,
                "Taxes": taxes,
                "D&A": da,
                "CapEx": capex,
                "NWC": nwc_level,
                "Change NWC": change_nwc,
                "UFCF": ufcf
            }
            projections.append(row)
            
            self._log(f"{i+1:<5} | {curr_rev:,.0f} | {ebit:,.0f} | {taxes:,.0f} | {nopat:,.0f} | {da:,.0f} | {capex:,.0f} | {change_nwc:,.0f} | {ufcf:,.0f}")
            
            prev_nwc = nwc_level 
            
        self.projections = projections
        return projections

    def compute_intrinsic_value(self, wacc: float, terminal_growth_rate: float) -> float:
        """
        Pure calculation helper. Returns share price.
        Used for Sensitivity Analysis without printing side effects.
        """
        # 1. Re-calculate Projections (if needed, or assume base case projections stick)
        # Note: WACC/Growth don't change operating projections (Revenue/EBIT), 
        # only the discounting and TV. So we reuse self.projections if populated.
        if not self.projections:
            self.forecast_cash_flows()
            
        ufcfs = [p['UFCF'] for p in self.projections]
        if not ufcfs:
            return 0.0

        # 2. PV of Stage 1
        pv_ufcf_sum = 0.0
        for i, flow in enumerate(ufcfs):
            pv_ufcf_sum += flow / ((1 + wacc) ** (i + 1))
            
        # 3. PV of Terminal Value
        if wacc <= terminal_growth_rate:
            return 0.0 # Invalid scenario
            
        final_ufcf = ufcfs[-1]
        tv = (final_ufcf * (1 + terminal_growth_rate)) / (wacc - terminal_growth_rate)
        pv_tv = tv / ((1 + wacc) ** 5)
        
        # 4. Enterprise Value
        current_ev = pv_ufcf_sum + pv_tv
        
        # 5. Equity Value
        # EV_12m logic: (Current EV * (1+WACC)) - Year 1 Cash Flow
        ev_12m = (current_ev * (1 + wacc)) - ufcfs[0]
        
        total_debt = self.data.total_debt[-1] if self.data.total_debt else 0
        cats = self.data.cash_and_equivalents[-1] if self.data.cash_and_equivalents else 0
        net_debt = total_debt - cats
        
        equity_val = ev_12m - net_debt
        
        # 6. Per Share
        shares = self.data.shares_outstanding
        if shares <= 0:
            return 0.0
            
        return equity_val / shares

    def calculate_intrinsic_value(self) -> float:
        """
        PHASE 4 & 5: VALUATION & 12-MONTH TARGET PRICE BRIDGE
        (Main execution method with logging)
        """
        self._log(f"\n{'#'*60}")
        print(" STARTING VALUATION")
        self._log(f"{'#'*60}")

        # Step 1: WACC
        wacc = self.calculate_wacc()
        
        # Step 2: Forecast
        self.forecast_cash_flows()
        ufcfs = [p['UFCF'] for p in self.projections]
        
        if not ufcfs:
            return 0.0
            
        self._print_header("PHASE 4: DCF VALUATION")

        # Step 3: Discount Stage 1
        pv_ufcf_sum = 0
        self._log(f"{'Year':<5} | {'UFCF':<15} | {'Discount Fac':<12} | {'PV':<15}")
        self._log("-" * 60)
        
        for i, flow in enumerate(ufcfs):
            factor = (1 + wacc) ** (i + 1)
            pv = flow / factor
            pv_ufcf_sum += pv
            self._log(f"{i+1:<5} | {flow:,.0f} | {factor:.4f}       | {pv:,.0f}")
            
        self._log(f"{'-'*60}")
        self._log(f"Stage 1 PV Sum: ${pv_ufcf_sum:,.0f}")
        
        # Step 4: Terminal Value (Stage 2)
        final_ufcf = ufcfs[-1]
        g = self.assumptions.terminal_growth_rate
        
        tv = 0.0
        if wacc > g:
            tv = (final_ufcf * (1 + g)) / (wacc - g)
            self._log(f"\nTerminal Value Calculation (Gordon Growth):")
            self._log(f"   Final UFCF:   ${final_ufcf:,.0f}")
            self._log(f"   Growth (g):   {g:.2%}")
            self._log(f"   WACC:         {wacc:.4%}")
            self._log(f"   -> TV:        ${tv:,.0f}")
        else:
            self._log(f"Error: WACC ({wacc}) <= Terminal Growth ({g})")

        pv_tv = tv / ((1 + wacc) ** 5)
        self._log(f"Discounting TV 5 years back...")
        self._log(f"   PV of TV:     ${pv_tv:,.0f}")
        
        # Step 5: Current Enterprise Value
        current_ev = pv_ufcf_sum + pv_tv
        self._log(f"\n-> CURRENT ENTERPRISE VALUE: ${current_ev:,.0f}")
        
        # Step 6: PHASE 5 - THE 12-MONTH TARGET PRICE BRIDGE
        self._print_header("PHASE 5: 12-MONTH TARGET PRICE BRIDGE")
        
        self._log(f"1. Current Enterprise Value:     ${current_ev:,.0f}")
        self._log(f"2. Plus: Growth (1 Year @ WACC): +${current_ev * wacc:,.0f}")
        self._log(f"3. Less: Year 1 Cash Flow Paid:  -${ufcfs[0]:,.0f}")
        
        # EV_12m = (Current EV * (1+WACC)) - Year 1 Cash Flow
        ev_12m = (current_ev * (1 + wacc)) - ufcfs[0]
        self._log(f"-> 12-MONTH ENTERPRISE VALUE:    ${ev_12m:,.0f}")
        
        # Step 7: Equity Value
        total_debt = self.data.total_debt[-1] if self.data.total_debt else 0
        cash = self.data.cash_and_equivalents[-1] if self.data.cash_and_equivalents else 0
        net_debt = total_debt - cash
        
        self._log(f"\nNet Debt Calculation:")
        self._log(f"   Total Debt: ${total_debt:,.0f}")
        self._log(f"   Less Cash:  -${cash:,.0f}")
        self._log(f"   = Net Debt: ${net_debt:,.0f}")
        
        equity_value_12m = ev_12m - net_debt
        self._log(f"\n-> EQUIT VALUE (12m):            ${equity_value_12m:,.0f}")
        
        # Step 8: Target Price
        shares = self.data.shares_outstanding
        self._log(f"   Shares Outstanding:           {shares:,.0f}")
        
        if shares <= 0:
            return 0.0
            
        target_price = equity_value_12m / shares
        
        self._print_header(f"FINAL TARGET PRICE: ${target_price:.2f}")
        
        return round(target_price, 2)

    def generate_sensitivity_table(self):
        """
        Generates a 5x5 Matrix of Target Prices.
        Rows: WACC (+- 0.5% steps)
        Cols: Terminal Growth (+- 1.0% steps)
        """
        base_wacc = self.wacc
        base_g = self.assumptions.terminal_growth_rate
        
        # Ranges
        wacc_steps = [base_wacc - 0.01, base_wacc - 0.005, base_wacc, base_wacc + 0.005, base_wacc + 0.01]
        g_steps =    [base_g - 0.02, base_g - 0.01, base_g, base_g + 0.01, base_g + 0.02]
        
        matrix = []
        for w in wacc_steps:
            row = []
            for g in g_steps:
                price = self.compute_intrinsic_value(w, g)
                row.append(price)
            matrix.append((w, row))
            
        return g_steps, matrix

# --- Example Usage (Commented out until implemented) ---
# data = FinancialData(revenue=[100,110,120], ...)
# assumptions = DCFAssumptions(revenue_growth_rates=[...], ...)
# model = DCFModel(data, assumptions)
# value = model.calculate_intrinsic_value()
# self._log(f"Intrinsic Value: ${value}")

