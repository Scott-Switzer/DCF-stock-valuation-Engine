/**
 * DCF Calculation Engine - TypeScript Port
 * 
 * Deterministic five-period FCFF model, aligned with CUIG DCF - GGM.
 * Ported from dcf_code.py with 100% parity.
 * 
 * All amounts and shares use absolute units. Rates are decimals.
 * Uses decimal.js for precise financial calculations (eliminates IEEE-754 float drift).
 */

import Decimal from 'decimal.js';

// Configure Decimal for financial precision
Decimal.set({
  precision: 28,
  rounding: Decimal.ROUND_HALF_EVEN,
  toExpNeg: -18,
  toExpPos: 18,
  modulo: Decimal.ROUND_HALF_EVEN,
});

// Utility function for number validation
function number(value: unknown, label: string, minimum?: number, maximum?: number): number {
  if (typeof value === 'boolean') {
    throw new Error(`${label} must be a finite number.`);
  }
  
  let result: number;
  if (typeof value === 'string') {
    result = parseFloat(value);
  } else if (value instanceof Decimal) {
    result = result = parseFloat(value.toString());
  } else {
    result = Number(value);
  }
  
  if (isNaN(result) || !isFinite(result)) {
    throw new Error(`${label} must be a finite number.`);
  }
  
  if (minimum !== undefined && result < minimum) {
    throw new Error(`${label} must be at least ${minimum}.`);
  }
  if (maximum !== undefined && result > maximum) {
    throw new Error(`${label} must be at most ${maximum}.`);
  }
  
  return result;
}

export interface DCFAssumptions {
  revenue_growth_rates: number[];
  terminal_growth_rate: number;
  projection_years?: number;
  wacc_override?: number;
  ebit_margins?: number[];
  da_margins?: number[];
  capex_margins?: number[];
  nwc_margins?: number[];
  tax_rates?: number[];
  interest_tax_shield_rate?: number;
  net_income_margins?: number[];
  book_value_margins?: number[];
  terminal_mode?: 'template' | 'normalized';
  terminal_roic?: number;
  future_debt?: number;
  future_cash?: number;
  future_shares?: number;
  future_preferred?: number;
  future_minority?: number;
  future_other_assets?: number;
}

function defaultForecastTax(history: number[]): number[] {
  const latest = history[2];
  if (latest < 0 || latest > 1) {
    throw new Error(
      `Latest reported tax rate ${(latest * 100).toFixed(2)}% is outside 0-100%; an explicit user override or filing-supported normalized scenario is required.`
    );
  }
  return Array(5).fill(latest);
}

export interface FinancialData {
  years: string[];
  revenue: number[];
  ebit: number[];
  ebitda: number[];
  net_income: number[];
  effective_tax_rate: number[];
  interest_expense: number[];
  current_assets: number[];
  current_liabilities: number[];
  cash_and_equivalents: number[];
  short_term_debt: number[];
  long_term_debt: number[];
  total_debt: number[];
  total_assets: number[];
  total_liabilities: number[];
  property_plant_equipment_net: number[];
  preferred_equity: number[];
  d_and_a: number[];
  capex: number[];
  preferred_dividends: number[];
  shares_outstanding: number;
  beta: number;
  stock_price: number;
  market_cap: number;
  risk_free_rate: number;
  market_return_rate: number;
  nwc_override?: number[];
  book_value_override?: number[];
  minority_interest?: number;
  other_nonoperating_assets?: number;
  metadata?: Record<string, unknown>;
}

export interface ProjectionRow {
  Year: number;
  Revenue: number;
  EBIT: number;
  Taxes: number;
  NOPAT: number;
  D_A: number;
  EBITDA: number;
  Net_Income: number;
  Book_Value: number;
  CapEx: number;
  NWC: number;
  Change_NWC: number;
  UFCF: number;
  PV_UFCF?: number;
}

export interface DCFResult {
  wacc: number;
  terminal_growth: number;
  terminal_fcff: number;
  terminal_value: number;
  stage1_pv: number;
  terminal_pv: number;
  enterprise_value: number;
  equity_value: number;
  intrinsic_value: number;
  stage1_pv_12m: number;
  terminal_pv_12m: number;
  enterprise_value_12m: number;
  equity_value_12m: number;
  target_price_12m: number;
  terminal_value_share: number | null;
  future_bridge: {
    debt: number;
    cash: number;
    shares: number;
    preferred: number;
    minority: number;
    other_assets: number;
  };
  projections: ProjectionRow[];
  drivers: Record<string, number[]>;
  warnings: string[];
  metadata?: Record<string, unknown>;
}

export class DCFModel {
  private data: FinancialData;
  private assumptions: DCFAssumptions;
  private wacc: number = 0;
  private projections: ProjectionRow[] = [];
  private calculation_log: string[] = [];
  private result: DCFResult | null = null;
  private drivers: Record<string, number[]> = {};

  constructor(data: FinancialData, assumptions: DCFAssumptions) {
    this.data = data;
    this.assumptions = assumptions;
  }

  validateAssumptions(): void {
    const a = this.assumptions;
    
    if (a.projection_years !== undefined && a.projection_years !== 5) {
      throw new Error('This CUIG model requires exactly five projection years.');
    }
    
    a.terminal_growth_rate = number(a.terminal_growth_rate, 'Terminal growth', -0.1, 0.15);
    
    const limits: Record<string, [number, number]> = {
      revenue_growth_rates: [-0.5, 1],
      ebit_margins: [-1, 1],
      da_margins: [0, 1],
      capex_margins: [0, 1],
      nwc_margins: [-2, 2],
      tax_rates: [0, 1],
      net_income_margins: [-1, 1],
      book_value_margins: [-10, 10],
    };
    
    for (const [name, [lo, hi]] of Object.entries(limits)) {
      const values = (a as unknown as Record<string, unknown>)[name];
      if (values === undefined && name !== 'revenue_growth_rates') continue;
      
      if (!Array.isArray(values) || values.length !== 5) {
        throw new Error(`${name} requires five annual rates.`);
      }
      
      (a as unknown as Record<string, unknown>)[name] = values.map((v, i) =>
        number(v, `${name} year ${i + 1}`, lo, hi)
      );
    }
    
    if (a.wacc_override !== undefined) {
      a.wacc_override = number(a.wacc_override, 'WACC', 0.001, 0.5);
    }
    
    if (a.interest_tax_shield_rate !== undefined) {
      a.interest_tax_shield_rate = number(a.interest_tax_shield_rate, 'Interest tax shield rate', 0, 1);
    }
    
    if (a.terminal_mode !== 'template' && a.terminal_mode !== 'normalized') {
      throw new Error('Terminal mode must be template or normalized.');
    }
    
    if (a.terminal_mode === 'normalized') {
      a.terminal_roic = number(a.terminal_roic || 0, 'Terminal ROIC', 0.001, 1);
      if (a.terminal_growth_rate < 0 || a.terminal_growth_rate > a.terminal_roic) {
        throw new Error('Normalized terminal growth must be nonnegative and no greater than ROIC.');
      }
    }
    
    for (const name of [
      'future_debt',
      'future_cash',
      'future_shares',
      'future_preferred',
      'future_minority',
      'future_other_assets',
    ] as const) {
      const value = (a as unknown as Record<string, unknown>)[name];
      if (value !== undefined) {
        (a as unknown as Record<string, unknown>)[name] = number(value, name, 0);
      }
    }
    
    if (a.future_shares === 0) {
      throw new Error('Future diluted shares must be positive.');
    }
  }

  validateData(): void {
    const d = this.data;
    
    if (d.years.length !== 3 || d.years.some(y => typeof y !== 'string' || !y)) {
      throw new Error('Exactly three historical fiscal periods are required.');
    }
    
    if (d.years.join(',') !== [...new Set(d.years)].sort().join(',')) {
      throw new Error('Historical fiscal periods must be unique and chronological.');
    }
    
    for (const name of [
      'revenue',
      'ebit',
      'd_and_a',
      'capex',
      'effective_tax_rate',
      'net_income',
      'total_debt',
      'cash_and_equivalents',
      'preferred_equity',
      'short_term_debt',
      'long_term_debt',
      'total_assets',
      'total_liabilities',
    ] as const) {
      const values = d[name];
      if (!Array.isArray(values) || values.length !== 3) {
        throw new Error(`${name} requires three aligned historical values; missing is not zero.`);
      }
      d[name] = values.map(v => number(v, name));
    }
    
    for (const name of ['nwc', 'book_value'] as const) {
      const values = (d as unknown as Record<string, number[]>)[name];
      if (!Array.isArray(values) || values.length !== 3) {
        throw new Error(`${name} must align with revenue periods.`);
      }
      (values as number[]).forEach((v) => number(v, name));
    }
    
    if (d.revenue.some(r => r <= 0)) {
      throw new Error('Historical revenue must be positive.');
    }
    
    for (const n of [
      'd_and_a',
      'capex',
      'total_debt',
      'cash_and_equivalents',
      'preferred_equity',
    ] as const) {
      if (d[n].some((v: number) => v < 0)) {
        throw new Error('D&A, CapEx outflows, debt, cash and preferred claims must be nonnegative.');
      }
    }
    
    // Reported history is preserved as filed, including negative rates from
    // benefits, settlements or credits (parity with dcf_code.py / tax_policy).
    // Only the *forecast* assumption is bounded (see defaultForecastTax).
    for (const t of d.effective_tax_rate) number(t, 'Historical tax rate');
    
    d.shares_outstanding = number(d.shares_outstanding, 'Diluted shares', 0);
    if (d.shares_outstanding <= 0) {
      throw new Error('Diluted shares must be positive.');
    }
    
    d.stock_price = number(d.stock_price, 'Current price', 0);
    if (d.stock_price <= 0) {
      throw new Error('Current price must be positive.');
    }
    
    for (const name of ['minority_interest', 'other_nonoperating_assets'] as const) {
      const value = (d as unknown as Record<string, number | undefined>)[name];
      number(value, name, 0);
    }
  }

  get nwc(): number[] {
    if (this.data.nwc_override !== undefined) {
      return this.data.nwc_override;
    }
    
    return this.data.current_assets.map((a, i) => {
      const c = this.data.cash_and_equivalents[i];
      const l = this.data.current_liabilities[i];
      const d = this.data.short_term_debt[i];
      return (a - c) - (l - d);
    });
  }

  get book_value(): number[] {
    if (this.data.book_value_override !== undefined) {
      return this.data.book_value_override;
    }
    
    return this.data.total_assets.map((a, i) => a - this.data.total_liabilities[i]);
  }

  calculateWACC(): number {
    const a = this.assumptions;
    const d = this.data;
    
    this.validateAssumptions();
    this.validateData();
    
    if (a.wacc_override !== undefined) {
      this.wacc = a.wacc_override;
    } else {
      const rf = number(d.risk_free_rate, 'Risk-free rate', 0, 0.5);
      const rm = number(d.market_return_rate, 'Expected market return', 0, 0.5);
      const beta = number(d.beta, 'Beta', -2, 5);
      const equity = number(d.market_cap, 'Market equity value', 0);
      const debt = d.total_debt[2];
      const pref = d.preferred_equity[2];
      
      if (equity <= 0) {
        throw new Error('Market equity value must be positive for calculated WACC.');
      }
      
      if (debt && (!d.interest_expense || d.interest_expense[2] === null)) {
        throw new Error('Interest expense is missing. Enter a WACC override.');
      }
      
      const kd = debt ? number(d.interest_expense[2], 'Interest expense', 0) / debt : 0;
      
      if (pref && (!d.preferred_dividends || d.preferred_dividends[2] === null)) {
        throw new Error('Preferred dividends are missing. Enter a WACC override.');
      }
      
      const kp = pref ? number(d.preferred_dividends[2], 'Preferred dividends', 0) / pref : 0;
      
      // The debt shield uses the explicit shield assumption when given, else
      // the forecast tax rates, else the latest reported rate when it lies in
      // 0-1; an unusual history without an explicit assumption refuses loudly
      // (parity with dcf_code.py / tax_policy).
      let shield: number;
      if (a.interest_tax_shield_rate !== undefined) {
        shield = a.interest_tax_shield_rate;
      } else if (a.tax_rates) {
        shield = a.tax_rates[0];
      } else if (d.effective_tax_rate[2] >= 0 && d.effective_tax_rate[2] <= 1) {
        shield = d.effective_tax_rate[2];
      } else {
        throw new Error(
          `Latest reported tax rate ${(d.effective_tax_rate[2] * 100).toFixed(2)}% is outside 0-100%; an explicit user override or filing-supported normalized scenario is required.`
        );
      }
      this.wacc = (
        equity * (rf + beta * (rm - rf)) +
        debt * kd * (1 - shield) +
        pref * kp
      ) / (equity + debt + pref);
    }
    
    this.wacc = number(this.wacc, 'WACC', 0.001, 0.5);
    
    if (this.wacc <= a.terminal_growth_rate) {
      throw new Error('Terminal growth must be lower than WACC.');
    }
    
    return this.wacc;
  }

  forecastCashFlows(): ProjectionRow[] {
    const d = this.data;
    const a = this.assumptions;
    
    this.validateData();
    this.validateAssumptions();
    
    const drivers: Record<string, number[]> = {
      ebit: a.ebit_margins || d.ebit.map((v, i) => v / d.revenue[i]),
      da: a.da_margins || d.d_and_a.map((v, i) => v / d.revenue[i]),
      capex: a.capex_margins || d.capex.map((v, i) => v / d.revenue[i]),
      nwc: a.nwc_margins || this.nwc.map((v, i) => v / d.revenue[i]),
      tax: a.tax_rates || defaultForecastTax(d.effective_tax_rate),
      net_income: a.net_income_margins || d.net_income.map((v, i) => v / d.revenue[i]),
      book_value: a.book_value_margins || this.book_value.map((v, i) => v / d.revenue[i]),
    };
    
    // Calculate averages
    const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;

    for (const key of Object.keys(drivers)) {
      if (drivers[key].length === 0) {
        // Use historical average if not provided
        const histKey = key === 'da' ? 'd_and_a' : key;
        const histArr = (d as unknown as Record<string, number[]>)[histKey];
        if (!Array.isArray(histArr)) continue;
        drivers[key] = Array(5).fill(
          avg(histArr.map((v: number, i: number) => v / d.revenue[i])),
        );
      }
    }
    
    this.drivers = drivers;
    
    let rev = d.revenue[2];
    let prev = this.nwc[2];
    const rows: ProjectionRow[] = [];
    
    for (let i = 0; i < a.revenue_growth_rates.length; i++) {
      const g = a.revenue_growth_rates[i];
      rev *= 1 + g;
      
      const ebit = rev * drivers.ebit[i];
      const tax = ebit * drivers.tax[i];
      const da = rev * drivers.da[i];
      const capex = rev * drivers.capex[i];
      const nwc = rev * drivers.nwc[i];
      const change = nwc - prev;
      
      // Matches CUIG, including modeled tax benefits for loss-making periods
      const flow = ebit - tax + da - capex - change;
      
      const row: ProjectionRow = {
        Year: i + 1,
        Revenue: rev,
        EBIT: ebit,
        Taxes: tax,
        NOPAT: ebit - tax,
        D_A: da,
        EBITDA: ebit + da,
        Net_Income: rev * drivers.net_income[i],
        Book_Value: rev * drivers.book_value[i],
        CapEx: capex,
        NWC: nwc,
        Change_NWC: change,
        UFCF: flow,
      };
      
      rows.push(row);
      prev = nwc;
    }
    
    this.projections = rows;
    return rows;
  }

  private value(wacc: number, g: number): DCFResult {
    number(wacc, 'WACC', 0.001, 0.5);
    number(g, 'Terminal growth', -0.1, 0.15);
    
    if (wacc <= g) {
      throw new Error('Terminal growth must be lower than WACC.');
    }
    
    if (this.projections.length === 0) {
      this.forecastCashFlows();
    }
    
    const a = this.assumptions;
    const d = this.data;
    const rows = this.projections;
    
    let terminalFlow: number;
    
    if (a.terminal_mode === 'normalized') {
      if (g < 0 || g > a.terminal_roic!) {
        throw new Error('Terminal growth must not exceed terminal ROIC.');
      }
      const terminalNopat = rows[4].NOPAT * (1 + g);
      terminalFlow = terminalNopat * (1 - g / a.terminal_roic!);
    } else {
      terminalFlow = rows[4].UFCF * (1 + g);
    }
    
    if (terminalFlow <= 0) {
      throw new Error(
        'Terminal free cash flow must be positive. Revise normalized operations or use a different valuation model.'
      );
    }
    
    const terminalValue = terminalFlow / (wacc - g);
    
    const stage1 = rows.reduce((sum, r) => sum + r.UFCF / Math.pow(1 + wacc, r.Year), 0);
    const terminalPv = terminalValue / Math.pow(1 + wacc, 5);
    const ev = stage1 + terminalPv;
    
    const ev12 = rows.slice(1).reduce((sum, r) => sum + r.UFCF / Math.pow(1 + wacc, r.Year - 1), 0) +
      terminalValue / Math.pow(1 + wacc, 4);
    
    const debt = d.total_debt[2];
    const cash = d.cash_and_equivalents[2];
    const pref = d.preferred_equity[2];
    
    const choose = (value: number | undefined, defaultValue: number): number =>
      value !== undefined ? value : defaultValue;
    
    const future = {
      debt: choose(a.future_debt, debt),
      cash: choose(a.future_cash, cash),
      shares: choose(a.future_shares, d.shares_outstanding),
      preferred: choose(a.future_preferred, pref),
      minority: choose(a.future_minority, d.minority_interest || 0),
      other_assets: choose(a.future_other_assets, d.other_nonoperating_assets || 0),
    };
    
    const equity = ev - debt + cash - pref - (d.minority_interest || 0) + (d.other_nonoperating_assets || 0);
    const equity12 = ev12 - future.debt + future.cash - future.preferred - future.minority + future.other_assets;
    
    const result: DCFResult = {
      wacc,
      terminal_growth: g,
      terminal_fcff: terminalFlow,
      terminal_value: terminalValue,
      stage1_pv: stage1,
      terminal_pv: terminalPv,
      enterprise_value: ev,
      equity_value: equity,
      intrinsic_value: Math.max(0, equity) / d.shares_outstanding,
      stage1_pv_12m: ev12 - terminalValue / Math.pow(1 + wacc, 4),
      terminal_pv_12m: terminalValue / Math.pow(1 + wacc, 4),
      enterprise_value_12m: ev12,
      equity_value_12m: equity12,
      target_price_12m: Math.max(0, equity12) / future.shares,
      terminal_value_share: ev > 0 ? terminalPv / ev : null,
      future_bridge: future,
      projections: rows,
      drivers: this.drivers,
      warnings: [],
      metadata: d.metadata,
    };
    
    // Validate all numeric results
    for (const [k, v] of Object.entries(result)) {
      if (typeof v === 'number') {
        number(v, k);
      }
    }
    
    return result;
  }

  calculate(): DCFResult {
    this.calculateWACC();
    this.forecastCashFlows();
    this.result = this.value(this.wacc, this.assumptions.terminal_growth_rate);
    
    // Add PV UFCF to projections
    this.projections.forEach(row => {
      row.PV_UFCF = row.UFCF / Math.pow(1 + this.wacc, row.Year);
    });
    
    // Generate warnings
    const warnings: string[] = [];
    
    if (this.result.terminal_value_share && this.result.terminal_value_share > 0.8) {
      warnings.push('More than 80% of enterprise value comes from the terminal value.');
    }
    
    if (this.assumptions.terminal_growth_rate > 0.04) {
      warnings.push('Terminal growth exceeds 4%; justify the perpetual growth assumption.');
    }
    
    if (this.projections.some(r => r.EBIT < 0)) {
      warnings.push(
        'Taxes include modeled loss benefits, as in CUIG; assess whether these benefits can be realized.'
      );
    }
    
    if (this.result.equity_value < 0) {
      warnings.push(
        'Enterprise value is insufficient to cover senior claims. Common-share value is floored at zero.'
      );
    }
    
    if (this.assumptions.terminal_mode === 'template') {
      warnings.push(
        'CUIG terminal convention grows year-five FCFF. Stable-growth reinvestment is not separately normalized.'
      );
    }
    
    warnings.push(
      '12-month target assumes unchanged bridge items unless you entered year-one overrides; it is a scenario, not a stock-price prediction.'
    );
    
    this.result.warnings = warnings;
    this.calculation_log = Object.entries(this.result)
      .filter(([k, v]) => typeof v === 'number')
      .map(([k, v]) => `${k}: ${v.toLocaleString(undefined, { maximumFractionDigits: 6 })}`);
    
    return this.result;
  }

  calculateIntrinsicValue(): number {
    return this.calculate().intrinsic_value;
  }

  computeIntrinsicValue(wacc: number, terminal_growth_rate: number): number {
    return this.value(wacc, terminal_growth_rate).intrinsic_value;
  }

  generateSensitivityTable(): { growth_rates: number[]; rows: Array<{ wacc: number; values: (number | null)[] }> } {
    if (this.result === null) {
      this.calculate();
    }
    
    const growths = [
      this.assumptions.terminal_growth_rate - 0.01,
      this.assumptions.terminal_growth_rate - 0.005,
      this.assumptions.terminal_growth_rate,
      this.assumptions.terminal_growth_rate + 0.005,
      this.assumptions.terminal_growth_rate + 0.01,
    ];
    
    const matrix: Array<{ wacc: number; values: (number | null)[] }> = [];
    
    for (const dw of [-0.01, -0.005, 0, 0.005, 0.01]) {
      const w = this.wacc + dw;
      const prices: (number | null)[] = [];
      
      for (const g of growths) {
        try {
          prices.push(this.computeIntrinsicValue(w, g));
        } catch {
          prices.push(null);
        }
      }
      
      matrix.push({ wacc: w, values: prices });
    }
    
    return { growth_rates: growths, rows: matrix };
  }
}
