// Public primary-source reviews. These are drivers and gates, not forecast defaults.
export const researchReviews={
 EVTC:{cik:'0001559865',reviewed_at:'2026-10-21',latest_operating_period:'2026-06-30',status:'CURRENT_DRIVERS_IDENTIFIED_FORECAST_NOT_BUILT',
  drivers:['Latin America growth includes acquisitions and currency effects; separate organic and acquired growth.', 'The 2026 acquisition changes capital claims. Reconcile current non-controlling interests before using an annual equity bridge.', 'Adjusted EBITDA margin and adjusted tax guidance are non-GAAP; do not substitute them for GAAP EBIT margin or cash taxes.'],
  required_repairs:['CURRENT_CAPITAL_CLAIMS_RECONCILIATION','GAAP_FORECAST_BRIDGE','DATED_COMPANY_DISCOUNT_RATE','CURRENT_SECURITY_PRICE_BRIDGE'],
  citations:[{url:'https://www.sec.gov/Archives/edgar/data/1559865/000155986526000043/ex991063026.htm',published_at:'2026-08-04',section:'Second Quarter 2026 Results and 2026 Outlook'}, {url:'https://www.sec.gov/Archives/edgar/data/1559865/000155986526000047/evtc-20260630.htm',period_end:'2026-06-30',section:'Basis of presentation, acquisitions and capital claims'}]},
 APTV:{cik:'0001521332',reviewed_at:'2026-10-21',latest_operating_period:'2026-06-30',status:'STRUCTURAL_BREAK_REQUIRES_REBASED_HISTORY',
  drivers:['The Electrical Distribution Systems business was spun off as Versigent on April 1, 2026.', 'Rebase operating history to continuing operations; pre-spin consolidated revenue is not the current business.', 'The spin-off dividend and associated debt redemptions require a current capital bridge.'],
  required_repairs:['POST_SPIN_CONTINUING_OPERATIONS_HISTORY','POST_SPIN_CAPITAL_CLAIMS','DATED_COMPANY_DISCOUNT_RATE','CURRENT_SECURITY_PRICE_BRIDGE'],
  citations:[{url:'https://www.sec.gov/Archives/edgar/data/1521332/000152133226000061/aptv-20260630.htm',period_end:'2026-06-30',section:'Separation of Electrical Distribution Systems'}, {url:'https://ir.aptiv.com/news/news-details/2026/Aptiv-Reports-Second-Quarter-2026-Financial-Results/default.aspx',published_at:'2026-08-04',section:'Continuing operations and spin-off financing'}]},
 PEP:{cik:'0000077476',reviewed_at:'2026-10-21',latest_operating_period:'2026-09-05',status:'NEWER_THAN_STORED_SEC_CUTOFF_REFRESH_REQUIRED',
  drivers:['Third-quarter results were published after the stored September SEC cutoff; refresh operating context before forecasting.', 'Separate acquisition and currency effects from organic growth, and North American pricing and volume from international growth.', 'GAAP profit comparisons include prior-year impairments and current comparability items; reconcile a normalized operating base.'],
  required_repairs:['POST_CUTOFF_QUARTERLY_INPUTS','NORMALIZED_GAAP_OPERATING_BASE','DATED_COMPANY_DISCOUNT_RATE','CURRENT_SECURITY_PRICE_BRIDGE'],
  citations:[{url:'https://www.sec.gov/Archives/edgar/data/77476/000007747626000050/q320268-kxexhibit991.htm',published_at:'2026-10-08',section:'Third-Quarter Results Discussion and Guidance'}]},
 FLS:{cik:'0000030625',reviewed_at:'2026-10-21',latest_operating_period:'2026-06-30',status:'CURRENT_DRIVERS_IDENTIFIED_FORECAST_NOT_BUILT',
  drivers:['Bookings and backlog growth do not imply immediate revenue growth; use conversion timing.', 'Current organic sales guidance reflects Middle East disruption, while reported sales include acquisition and currency benefits.', 'Reconcile reported and adjusted margins, acquisition financing and capital expenditure guidance separately.'],
  required_repairs:['BACKLOG_CONVERSION_FORECAST','CURRENT_ACQUISITION_CAPITAL_BRIDGE','DATED_COMPANY_DISCOUNT_RATE','CURRENT_SECURITY_PRICE_BRIDGE'],
  citations:[{url:'https://www.sec.gov/Archives/edgar/data/30625/000119312526323649/d15165dex991.htm',published_at:'2026-07-29',section:'Management Commentary and 2026 Guidance'}]},
 PH:{cik:'0000076334',reviewed_at:'2026-10-21',latest_operating_period:'2026-06-30',status:'CURRENT_DRIVERS_IDENTIFIED_FORECAST_NOT_BUILT',
  drivers:['Forecast by the June fiscal year end and distinguish organic industrial recovery from acquisition effects.', 'Fiscal 2027 guidance excludes pending acquisitions; do not include their sales without purchase financing and integration costs.', 'Long-term segment margin and free-cash-flow targets are management targets, not realized GAAP consolidated EBIT margins.'],
  required_repairs:['FISCAL_YEAR_ALIGNED_FORECAST','ACQUISITION_SCENARIO_SEPARATION','CONSOLIDATED_GAAP_MARGIN_BRIDGE','DATED_COMPANY_DISCOUNT_RATE','CURRENT_SECURITY_PRICE_BRIDGE'],
  citations:[{url:'https://investors.parker.com/news-events/press-releases/detail/509/parker-reports-record-fiscal-2026-fourth-quarter-and-full',published_at:'2026-08-06',section:'Fiscal 2027 Outlook and GAAP/non-GAAP reconciliations'}]}

};
