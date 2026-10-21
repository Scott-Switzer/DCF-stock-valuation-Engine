// Public primary-source reviews. These are drivers and gates, not forecast defaults.
export const researchReviews={
 EVTC:{reviewed_at:'2026-10-21',latest_operating_period:'2026-06-30',status:'CURRENT_DRIVERS_IDENTIFIED_FORECAST_NOT_APPROVED',
  drivers:['Latin America growth includes acquisitions and currency effects; separate organic and acquired growth.', 'The 2026 acquisition changes capital claims. Reconcile current non-controlling interests before using an annual equity bridge.', 'Adjusted EBITDA margin and adjusted tax guidance are non-GAAP; do not substitute them for GAAP EBIT margin or cash taxes.'],
  required_repairs:['CURRENT_CAPITAL_CLAIMS_RECONCILIATION','GAAP_FORECAST_BRIDGE','DATED_COMPANY_DISCOUNT_RATE','CURRENT_SECURITY_PRICE_BRIDGE'],
  citations:[{url:'https://www.sec.gov/Archives/edgar/data/1559865/000155986526000043/ex991063026.htm',published_at:'2026-08-04',section:'Second Quarter 2026 Results and 2026 Outlook'}, {url:'https://www.sec.gov/Archives/edgar/data/1559865/000155986526000047/evtc-20260630.htm',period_end:'2026-06-30',section:'Basis of presentation, acquisitions and capital claims'}]},
 APTV:{reviewed_at:'2026-10-21',latest_operating_period:'2026-06-30',status:'STRUCTURAL_BREAK_REQUIRES_REBASED_HISTORY',
  drivers:['The Electrical Distribution Systems business was spun off as Versigent on April 1, 2026.', 'Rebase operating history to continuing operations; pre-spin consolidated revenue is not the current business.', 'The spin-off dividend and associated debt redemptions require a current capital bridge.'],
  required_repairs:['POST_SPIN_CONTINUING_OPERATIONS_HISTORY','POST_SPIN_CAPITAL_CLAIMS','DATED_COMPANY_DISCOUNT_RATE','CURRENT_SECURITY_PRICE_BRIDGE'],
  citations:[{url:'https://www.sec.gov/Archives/edgar/data/1521332/000152133226000061/aptv-20260630.htm',period_end:'2026-06-30',section:'Separation of Electrical Distribution Systems'}, {url:'https://ir.aptiv.com/news/news-details/2026/Aptiv-Reports-Second-Quarter-2026-Financial-Results/default.aspx',published_at:'2026-08-04',section:'Continuing operations and spin-off financing'}]}
};
