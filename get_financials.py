import requests
import json

# Ask for ticker and convert to uppercase
ticker = input("Ticker? ").upper()

def get_fmp_data(endpoint: str, ticker: str, limit=3, period="annual"):
    base_url = f'https://financialmodelingprep.com/api/v3/{endpoint}'
    try:
        response = requests.get(base_url, params={
            'symbol': ticker,
            'period': period,
            'limit': limit,
            'apikey': 'ZYjK98Nfrpy9Ek5oc8e8RyvIRoCSFoTD'
        })
        if response.status_code == 403:
            # Fallback for free/restricted plans that reject 'period'
            response = requests.get(base_url, params={
                'symbol': ticker,
                'limit': limit,
                'apikey': 'ZYjK98Nfrpy9Ek5oc8e8RyvIRoCSFoTD'
            })
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API Error for {endpoint}: {e}")
        print(f"📝 Please manually enter the data for {ticker}")
        return get_manual_data(endpoint, ticker, limit)

def get_manual_data(endpoint: str, ticker: str, limit: int):
    """Fallback to manual data entry when API fails"""
    print(f"\n--- Manual Data Entry for {ticker} {endpoint.replace('-', ' ').title()} ---")
    data = []
    
    for i in range(limit):
        year = input(f"Enter year {i+1} (most recent first): ")
        print(f"Entering data for {year}:")
        
        if 'income' in endpoint:
            revenue = float(input("Revenue: ") or "0")
            operating_income = float(input("Operating Income (EBIT): ") or "0")
            income_before_tax = float(input("Income Before Tax: ") or "0")
            income_tax_expense = float(input("Income Tax Expense: ") or "0")
            interest_expense = float(input("Interest Expense: ") or "0")
            
            data.append({
                'calendarYear': year,
                'revenue': revenue,
                'operatingIncome': operating_income,
                'incomeBeforeTax': income_before_tax,
                'incomeTaxExpense': income_tax_expense,
                'interestExpense': interest_expense
            })
            
        elif 'balance' in endpoint:
            total_current_assets = float(input("Total Current Assets: ") or "0")
            total_current_liabilities = float(input("Total Current Liabilities: ") or "0")
            cash_and_cash_equivalents = float(input("Cash and Cash Equivalents: ") or "0")
            short_term_debt = float(input("Short Term Debt: ") or "0")
            long_term_debt = float(input("Long Term Debt: ") or "0")
            total_debt = short_term_debt + long_term_debt
            
            data.append({
                'calendarYear': year,
                'totalCurrentAssets': total_current_assets,
                'totalCurrentLiabilities': total_current_liabilities,
                'cashAndCashEquivalents': cash_and_cash_equivalents,
                'shortTermDebt': short_term_debt,
                'longTermDebt': long_term_debt,
                'totalDebt': total_debt
            })
            
        elif 'cash-flow' in endpoint:
            depreciation_and_amortization = float(input("Depreciation & Amortization: ") or "0")
            capital_expenditure = float(input("Capital Expenditure (negative number): ") or "0")
            
            data.append({
                'calendarYear': year,
                'depreciationAndAmortization': depreciation_and_amortization,
                'capitalExpenditure': capital_expenditure
            })
    
    return data

# Try to pull data from API, fallback to manual entry
try:
    income_statement = get_fmp_data('income-statement', ticker, limit=3, period="annual")
    balance_sheet = get_fmp_data('balance-sheet-statement', ticker, limit=3, period="annual")
    cashflow_statement = get_fmp_data('cash-flow-statement', ticker, limit=3, period="annual")
except Exception as e:
    print(f"❌ Failed to fetch data from API: {e}")
    print("📝 Switching to manual data entry...")
    income_statement = get_manual_data('income-statement', ticker, 3)
    balance_sheet = get_manual_data('balance-sheet-statement', ticker, 3)
    cashflow_statement = get_manual_data('cash-flow-statement', ticker, 3)

# ENSURE data are ordered oldest→newest so the last element is the most recent year
income_statement   = sorted(income_statement, key=lambda x: x['calendarYear'])
balance_sheet      = sorted(balance_sheet, key=lambda x: x['calendarYear'])
cashflow_statement = sorted(cashflow_statement, key=lambda x: x['calendarYear'])


def get_dcf_inputs(income, balance, cashflow):
    """
    Builds a list of dictionaries with the metrics needed for DCF:
    revenue, EBIT, depreciation & amortization, capex, net working capital (NWC),
    NWC as a percentage of revenue, and effective tax rate.
    """
    inputs = []
    for i in range(3):
        year    = income[i].get('calendarYear')
        revenue = income[i].get('revenue', 0)
        ebit    = income[i].get('operatingIncome', 0)
        d_and_a = cashflow[i].get('depreciationAndAmortization', 0)
        # Take the absolute value of capex; it's usually negative in the CF statement
        capex   = abs(cashflow[i].get('capitalExpenditure', 0))
        ca      = balance[i].get('totalCurrentAssets', 0)
        cl      = balance[i].get('totalCurrentLiabilities', 0)
        cash    = balance[i].get('cashAndCashEquivalents', 0)
        std     = balance[i].get('shortTermDebt', 0)
        # Use non-cash net working capital: (CA - Cash) - (CL - Short-term Debt)
        nwc     = (ca - cash) - (cl - std)
        nwc_ratio = nwc / revenue if revenue else 0

        tax_exp = income[i].get('incomeTaxExpense', 0)
        pre_tax = income[i].get('incomeBeforeTax', 1)
        tax_rate = tax_exp / pre_tax if pre_tax else 0

        inputs.append({
            'Year': year,
            'Revenue': revenue,
            'EBIT': ebit,
            'D&A': d_and_a,
            'CapEx': capex,
            'NWC': nwc,
            'NWC %': nwc_ratio,
            'Tax Rate': round(tax_rate, 4)
        })
    return inputs

def compute_avg_margins(dcf_inputs):
    """
    Computes average margins from the historical input list.
    Returns a dictionary with EBIT margin, D&A %, CapEx %, NWC % and Tax rate.
    """
    ebit_margin = sum(row['EBIT'] / row['Revenue'] for row in dcf_inputs) / len(dcf_inputs)
    da_pct      = sum(row['D&A'] / row['Revenue'] for row in dcf_inputs) / len(dcf_inputs)
    capex_pct   = sum(row['CapEx'] / row['Revenue'] for row in dcf_inputs) / len(dcf_inputs)
    nwc_pct     = sum(row['NWC %'] for row in dcf_inputs) / len(dcf_inputs)
    tax_rate = dcf_inputs[-1]['Tax Rate']  # Use the most recent year's tax rate
    
    return {
        'EBIT Margin': ebit_margin,
        'D&A %': da_pct,
        'CapEx %': capex_pct,
        'NWC %': nwc_pct,
        'Tax Rate': tax_rate
    }

# Display the extracted historical data
print("\nExtracted DCF Inputs (last 3 years):")
dcf_inputs = get_dcf_inputs(income_statement, balance_sheet, cashflow_statement)
for row in dcf_inputs:
    print(row)

def get_growth_rates():
    """
    Prompts the user for five revenue growth rates (percentage inputs) and
    converts them to decimal form.
    """
    rev_g_rates = []
    for i in range(1, 6):
        g = float(input(f"What is the Year {i} Revenue growth rate? (% form)\n")) / 100
        rev_g_rates.append(g)
    return rev_g_rates

# Prompt user for growth rates
growth_rates = get_growth_rates()

def forecast_ufcf_dynamic(base_revenue, growth_rates, margins, base_nwc):
    """
    Forecasts unlevered free cash flow (UFCF) for each year given a base
    revenue, a list of growth rates, margin assumptions, and the base NWC.
    """
    forecast = []
    revenue  = base_revenue
    prev_nwc = base_nwc
    for i, g in enumerate(growth_rates):
        revenue *= (1 + g)
        ebit    = revenue * margins['EBIT Margin']
        taxes   = ebit * margins['Tax Rate']
        d_and_a = revenue * margins['D&A %']
        capex   = revenue * margins['CapEx %']
        # Forecast current NWC from revenue and NWC %
        nwc_current = revenue * margins['NWC %']
        change_nwc  = nwc_current - prev_nwc
        # Subtract the change in NWC in the UFCF formula
        ufcf = ebit - taxes + d_and_a - capex - change_nwc
        forecast.append({
            'Year': f'Year {i+1}',
            'Revenue': round(revenue, 2),
            'EBIT': round(ebit, 2),
            'Taxes': round(taxes, 2),
            'D&A': round(d_and_a, 2),
            'CapEx': round(capex, 2),
            'Change NWC': round(change_nwc, 2),
            'UFCF': round(ufcf, 2)
        })
        # Carry forward the NWC balance for the next loop iteration
        prev_nwc = nwc_current
    return forecast

# Compute margins and base values
# Compute margins and base values
margins      = compute_avg_margins(dcf_inputs)
base_revenue = dcf_inputs[-1]['Revenue']  # use the most recent fiscal year
base_nwc     = dcf_inputs[-1]['NWC']      # use the most recent NWC

# Forecast UFCFs (no change needed here)
forecasted_ufcfs = forecast_ufcf_dynamic(base_revenue, growth_rates, margins, base_nwc)



# Forecast UFCFs
forecasted_ufcfs = forecast_ufcf_dynamic(base_revenue, growth_rates, margins, base_nwc)

print("\nForecasted UFCFs:")
for row in forecasted_ufcfs:
    print(row)

# ---- WACC calculation ----
def get_company_profile(ticker):
    url = 'https://financialmodelingprep.com/api/v3/profile'
    try:
        response = requests.get(url, params={'symbol': ticker, 'apikey': 'ZYjK98Nfrpy9Ek5oc8e8RyvIRoCSFoTD'})
        response.raise_for_status()
        data = response.json()
        return data[0] if isinstance(data, list) else data
    except Exception as e:
        print(f"❌ API Error for profile: {e}")
        print("📝 Please manually enter company profile data:")
        beta = float(input("Beta (default 1.0): ") or "1.0")
        market_cap = float(input("Market Cap: ") or "0")
        price = float(input("Current Stock Price: ") or "0")
        shares_outstanding = float(input("Shares Outstanding: ") or "0")
        
        return {
            'beta': beta,
            'mktCap': market_cap,
            'price': price,
            'sharesOutstanding': shares_outstanding
        }

def calculate_wacc(profile, income_statement, balance_sheet, tax_rate, risk_free_rate=0.042, market_return=0.10):
    # CAPM: Cost of Equity
    beta = profile.get('beta', 1)
    cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)

    # Market cap
    market_cap = profile.get('mktCap', 0)

    # Cost of Debt (use most recent year)
    interest_expense = abs(income_statement[-1].get('interestExpense', 0))
    short_term_debt  = balance_sheet[-1].get('shortTermDebt', 0)
    long_term_debt   = balance_sheet[-1].get('longTermDebt', 0)
    total_debt       = short_term_debt + long_term_debt
    cost_of_debt     = interest_expense / total_debt if total_debt > 0 else 0

    # Capital structure weights
    total_value   = market_cap + total_debt
    equity_weight = market_cap / total_value if total_value > 0 else 0
    debt_weight   = total_debt / total_value if total_value > 0 else 0

    # Final WACC (apply tax shield to cost of debt)
    wacc = equity_weight * cost_of_equity + debt_weight * cost_of_debt * (1 - tax_rate)
    return round(wacc, 4)

profile  = get_company_profile(ticker)
tax_rate = margins['Tax Rate']
wacc     = calculate_wacc(profile, income_statement, balance_sheet, tax_rate)

print(f"\nCalculated WACC: {wacc * 100:.2f}%")
print("\nDiscounted UFCFs (WACC: {:.2%}):".format(wacc))

# Discount each UFCF to present value
discounted_ufcfs = []
for i, ufcf_row in enumerate(forecasted_ufcfs):
    discount_factor = (1 + wacc) ** (i + 1)
    pv = ufcf_row['UFCF'] / discount_factor
    discounted_ufcfs.append(pv)
    print(f"Year {i+1}: ${pv:,.2f}")

stage1_value = sum(discounted_ufcfs)
print(f"\nStage 1 DCF Value (Sum of discounted UFCFs): ${stage1_value:,.2f}")

# === Terminal Value Calculation ===
print("\n--- Terminal Value Calculation (Gordon Growth Method) ---")
lt_growth_rate_input = input("Enter long-term perpetuity growth rate (e.g., 2.3 for 2.3%): ")
lt_growth_rate = float(lt_growth_rate_input) / 100

final_ufcf = forecasted_ufcfs[-1]['UFCF']
terminal_value = final_ufcf * (1 + lt_growth_rate) / (wacc - lt_growth_rate)
discounted_terminal_value = terminal_value / ((1 + wacc) ** 5)

stage_1_value = sum(discounted_ufcfs)
enterprise_value = stage_1_value + discounted_terminal_value

print(f"\nYear 5 UFCF: ${final_ufcf:,.2f}")
print(f"Terminal Value (Year 5): ${terminal_value:,.2f}")
print(f"Discounted Terminal Value: ${discounted_terminal_value:,.2f}")
print(f"\nStage 1 Value (Discounted UFCFs): ${stage_1_value:,.2f}")
print(f"Stage 2 Value (Discounted Terminal Value): ${discounted_terminal_value:,.2f}")
print(f"Total Enterprise Value (EV): ${enterprise_value:,.2f}")

# --- Net Debt Calculation ---
try:
    bs_url = "https://financialmodelingprep.com/api/v3/balance-sheet-statement"
    balance_sheet_latest_resp = requests.get(bs_url, params={'symbol': ticker, 'limit': 1, 'apikey': 'ZYjK98Nfrpy9Ek5oc8e8RyvIRoCSFoTD'})
    balance_sheet_latest_resp.raise_for_status()
    balance_sheet_latest = balance_sheet_latest_resp.json()[0]
    total_debt = balance_sheet_latest.get("totalDebt", 0)
    cash = balance_sheet_latest.get("cashAndCashEquivalents", 0)
except Exception as e:
    print(f"❌ API Error for latest balance sheet: {e}")
    print("📝 Using data from historical balance sheet...")
    # Use the most recent year from our historical data
    total_debt = balance_sheet[-1].get("totalDebt", 0)
    cash = balance_sheet[-1].get("cashAndCashEquivalents", 0)

net_debt = total_debt - cash

# --- Outstanding shares retrieval ---
def get_outstanding_shares_from_profile(profile: dict):
    shares = profile.get('sharesOutstanding')
    if not shares:
        mkt_cap = profile.get('mktCap')
        price = profile.get('price')
        shares = (mkt_cap / price) if (mkt_cap and price) else None
    if shares and shares > 0:
        print(f"✅ Retrieved outstanding shares from profile: {int(shares):,}")
        return shares
    print("❌ Could not retrieve 'sharesOutstanding' from profile.")
    return None

shares_outstanding = get_outstanding_shares_from_profile(profile)

if shares_outstanding:
    equity_value = enterprise_value - net_debt
    intrinsic_value_per_share = equity_value / shares_outstanding
    print(f"\nNet Debt: ${net_debt:,.2f}")
    print(f"Shares Outstanding: {shares_outstanding:,.0f}")
    print(f"Equity Value: ${equity_value:,.2f}")
    print(f"\033[92mIntrinsic Value Per Share: ${intrinsic_value_per_share:,.2f}\033[0m")
else:
    print("⚠️ Could not retrieve shares outstanding. Cannot compute intrinsic value per share.")
