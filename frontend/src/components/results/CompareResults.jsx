import ResultCard from './ResultCard';
import { EDGE_COLORS, EDGE_LABELS } from '../../utils/colors';

function CompanyProfile({ company, label, personaColor }) {
  if (!company) return null;
  return (
    <div className="rounded-xl bg-white border border-surface-200 p-4 shadow-sm">
      <h3 className="font-semibold mb-2" style={{ color: personaColor }}>
        {label}: {company.name}
      </h3>
      <div className="grid grid-cols-2 gap-2 text-xs">
        {[
          ['Moat', company.moat_durability],
          ['Enterprise Ready', company.enterprise_readiness_score],
          ['Dev Adoption', company.developer_adoption_score],
          ['Product Maturity', company.product_maturity_score],
          ['Switching Cost', company.customer_switching_cost],
          ['Rev Predictability', company.revenue_predictability],
          ['Market Timing', company.market_timing_score],
          ['Op Improvement', company.operational_improvement_potential],
        ].filter(([, v]) => v != null).map(([label, val]) => (
          <div key={label} className="flex justify-between">
            <span className="text-surface-500">{label}</span>
            <span className="text-surface-800 font-mono">{typeof val === 'number' ? val.toFixed(1) : val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function CompareResults({ results, compareData, personaColor, query }) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-surface-800">
        <span style={{ color: personaColor }}>{query?.target_company}</span>
        {' vs '}
        <span style={{ color: personaColor }}>{query?.compare_company}</span>
      </h2>

      {/* Head-to-head profiles */}
      {compareData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <CompanyProfile company={compareData.company_a} label="A" personaColor={personaColor} />
          <CompanyProfile company={compareData.company_b} label="B" personaColor={personaColor} />
        </div>
      )}

      {/* Shared edges */}
      {compareData?.shared_edges?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-surface-500">Direct relationships:</span>
          {compareData.shared_edges.map((e, i) => {
            const color = EDGE_COLORS[e.rel_type] || '#6b7280';
            return (
              <span key={i} className="px-2 py-0.5 rounded text-[10px] font-medium" style={{ backgroundColor: `${color}15`, color }}>
                {EDGE_LABELS[e.rel_type] || e.rel_type} {e.strength != null && e.strength}
              </span>
            );
          })}
        </div>
      )}

      {/* Shared themes */}
      {compareData?.shared_themes?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-surface-500">Shared themes:</span>
          {compareData.shared_themes.map((t) => (
            <span key={t} className="px-2 py-0.5 rounded text-[10px] bg-surface-100 text-surface-600">
              {t.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      {/* Common competitors / ranked results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-surface-600">
            {compareData?.common_competitors?.length > 0 ? 'Common Competitors (ranked)' : 'Related Companies'}
          </h3>
          <div className="columns-1 md:columns-2 gap-3">
            {results.map((r) => (
              <div key={r.company_id} className="break-inside-avoid mb-3">
                <ResultCard result={r} personaColor={personaColor} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
