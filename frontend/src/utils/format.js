const ATTRIBUTE_LABELS = {
  moat_durability: 'Moat',
  free_cash_flow_positive: 'FCF',
  customer_switching_cost: 'Switching Cost',
  low_debt: 'Low Debt',
  revenue_predictability: 'Rev. Predictability',
  valuation_margin: 'Valuation',
  operating_margin: 'Op. Margin',
  operational_improvement_potential: 'Op. Improvement',
  enterprise_readiness_score: 'Enterprise Ready',
  developer_adoption_score: 'Dev. Adoption',
  market_timing_score: 'Market Timing',
  yoy_employee_growth: 'Employee Growth',
  github_stars_normalized: 'GitHub Stars',
  product_maturity_inverse: 'Early Stage',
  product_maturity_score: 'Product Maturity',
  partnership_fit: 'Partnership Fit',
  competitive_threat: 'Competitive Threat',
  partnership_count: 'Partnerships',
  small_enough_to_acquire: 'Acquirable Size',
  customer_switching_cost_inverse: 'Low Lock-in',
};

export function formatAttributeName(attr) {
  return ATTRIBUTE_LABELS[attr] || attr.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatScore(score) {
  if (score == null) return '—';
  return (score * 100).toFixed(0);
}

export function formatCompositeScore(score) {
  if (score == null) return '—';
  return score.toFixed(2);
}

export function formatMarketCap(b) {
  if (b == null) return '—';
  if (b >= 1000) return `$${(b / 1000).toFixed(1)}T`;
  if (b >= 1) return `$${b.toFixed(1)}B`;
  return `$${(b * 1000).toFixed(0)}M`;
}

export function formatElapsed(ms) {
  if (ms == null) return '';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
