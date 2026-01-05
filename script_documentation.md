# DCF Component Documentation

This document describes the three Python scripts that make up the DCF Valuation Engine. Use this guide when integrating these scripts into a web application.

## 1. System Requirements & Dependencies

### External Libraries (pip install)
*   `requests` (For API calls)
*   `numpy` (For vectorized math and margins)

### Environment Variables
*   **FMP API Key**: The scripts currently have the key hardcoded. For production/hosting, you should move `ZYjK...` to an environment variable or secure config.

---

## 2. File: `run_dcf.py` (The Executive Script)

**Purpose**: The entry point. Handles user interaction, orchestrates data loading, runs the model, and prints results.

*   **Inputs (User Interactive)**:
    1.  **Ticker Symbol**: String (e.g., "AAPL", "MSFT"). Defaults to "AAPL".
    2.  **Revenue Growth Rates (Years 1-5)**: Float (Decimal format, e.g., `0.05` for 5%).
    3.  **Terminal Growth Rate**: Float (Decimal format, e.g., `0.025` for 2.5%).

*   **Outputs**:
    *   Console Logs: Detailed step-by-step valuation logs.
    *   Final Value: "Calculated Target Price: $XX.XX" printed to stdout.

*   **Web Integration Note**: Replace the `input()` calls with values received from your frontend form.

---

## 3. File: `dcf_loader.py` (The Data Connector)

**Purpose**: Fetches live financial data from Financial Modeling Prep (FMP) and normalizes it.

*   **Inputs (Function Arguments)**:
    *   `ticker`: String (The company symbol to fetch).

*   **Inputs (External API)**:
    *   **Endpoints Used**:
        *   `/stable/income-statement` (Limit: 5 years)
        *   `/stable/balance-sheet-statement` (Limit: 5 years)
        *   `/stable/cash-flow-statement` (Limit: 5 years)
        *   `/stable/quote`
        *   `/stable/profile`
    *   **Fallbacks (Hardcoded due to API Plan Limits)**:
        *   Market Return: Defaults to `10.0%`
        *   Risk Free Rate: Defaults to `4.2%`

*   **Outputs (Return Object)**:
    *   Returns a `FinancialData` object (defined in `dcf_code.py`) containing cleaned lists of historical Revenue, EBIT, Debt, Cash, etc.

---

## 4. File: `dcf_code.py` (The Logic Core)

**Purpose**: Contains the standard formulas and logic class `DCFModel`. Does NOT perform I/O.

*   **Inputs (Class Initialization)**:
    *   `data`: The `FinancialData` object from the loader.
    *   `assumptions`: A `DCFAssumptions` object containing the user's growth rates.

*   **Key Logic Blocks**:
    *   `_calculate_historical_margins`: Averages last 3 years of EBIT, D&A, NWC, CapEx margins.
    *   `calculate_wacc`: Computes CAPM Cost of Equity + After-Tax Cost of Debt.
    *   `forecast_cash_flows`: Projects 5 years of Revenue and calculates UFCF (EBIT - Tax + D&A - CapEx - ChgNWC).
    *   `calculate_intrinsic_value`: Performs the specifics 12-Month Bridge valuation.

*   **Outputs**:
    *   **Return Value**: The final Intrinsic Value per share (Float).
    *   **Logs**: Extensive calculation details printed to standard out (stdout) for verification.

---

## Deployment Quick-Check

To host this on a website (e.g., Flask/Django/FastAPI):

1.  **Backend**: Create an endpoint (e.g., `POST /calculate-dcf`).
2.  **Request Body**:
    ```json
    {
      "ticker": "AAPL",
      "growth_rates": [0.05, 0.05, 0.04, 0.04, 0.03],
      "terminal_growth": 0.025
    }
    ```
3.  **Controller Logic**:
    *   Import `load_data_from_api` and `DCFModel`.
    *   Call `data = load_data_from_api(json['ticker'])`.
    *   Create `assumptions = DCFAssumptions(...)` from JSON data.
    *   Run `model = DCFModel(data, assumptions)`.
    *   Return `model.calculate_intrinsic_value()`.
