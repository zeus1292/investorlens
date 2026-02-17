import { PERSONA_COLORS } from '../../utils/colors';
import { formatCompositeScore } from '../../utils/format';

const PERSONA_ORDER = ['value_investor', 'pe_firm', 'growth_vc', 'strategic_acquirer', 'enterprise_buyer'];

export default function CrossPersonaTable({ allPersonas, activePersona }) {
  if (!allPersonas) return null;

  return (
    <div className="rounded-xl bg-surface-800 border border-surface-700 overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-700">
        <h3 className="text-sm font-medium text-surface-400">Cross-Persona Comparison</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-700">
              <th className="px-3 py-2 text-left text-xs text-surface-500 font-medium w-8">#</th>
              {PERSONA_ORDER.map((pName) => {
                const pd = allPersonas[pName];
                if (!pd) return null;
                const isActive = pName === activePersona;
                const color = PERSONA_COLORS[pName];
                return (
                  <th
                    key={pName}
                    className="px-3 py-2 text-left text-xs font-medium"
                    style={{ color, opacity: isActive ? 1 : 0.6 }}
                  >
                    {pd.persona_display}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {[0, 1, 2, 3, 4].map((idx) => (
              <tr key={idx} className="border-b border-surface-700/50 hover:bg-surface-700/30">
                <td className="px-3 py-2 text-xs text-surface-500">{idx + 1}</td>
                {PERSONA_ORDER.map((pName) => {
                  const pd = allPersonas[pName];
                  if (!pd) return <td key={pName} />;
                  const r = pd.top_results?.[idx];
                  if (!r) return <td key={pName} className="px-3 py-2 text-xs text-surface-600">—</td>;
                  const isActive = pName === activePersona;
                  return (
                    <td key={pName} className="px-3 py-2">
                      <div className={`text-xs ${isActive ? 'text-white font-medium' : 'text-surface-300'}`}>
                        {r.name}
                      </div>
                      <div className="text-[10px] text-surface-500 font-mono">
                        {formatCompositeScore(r.composite_score)}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
