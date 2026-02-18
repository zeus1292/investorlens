import { PERSONA_COLORS, PERSONA_BG_COLORS } from '../utils/colors';

const PERSONA_META = {
  value_investor: { icon: '🏛', short: 'Value', description: 'Moats, cash flow, switching costs' },
  pe_firm: { icon: '🏢', short: 'PE', description: 'Margins, operational upside, predictability' },
  growth_vc: { icon: '🚀', short: 'VC', description: 'Growth, developer adoption, market timing' },
  strategic_acquirer: { icon: '🎯', short: 'Acquirer', description: 'Tech differentiation, integration fit' },
  enterprise_buyer: { icon: '🏗', short: 'Buyer', description: 'Maturity, enterprise readiness, TCO' },
};

export default function PersonaSelector({ personas, active, onChange, compact = false }) {
  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        {personas.map((p) => {
          const meta = PERSONA_META[p.name] || { icon: '👤', short: p.display_name };
          const isActive = active === p.name;
          const color = PERSONA_COLORS[p.name];
          return (
            <button
              key={p.name}
              onClick={() => onChange(p.name)}
              title={p.description}
              className="px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer border"
              style={{
                backgroundColor: isActive ? color : 'transparent',
                borderColor: color,
                color: isActive ? '#fff' : color,
                opacity: isActive ? 1 : 0.7,
              }}
            >
              {meta.icon} {meta.short}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {personas.map((p) => {
        const meta = PERSONA_META[p.name] || { icon: '👤', short: p.display_name, description: '' };
        const isActive = active === p.name;
        const color = PERSONA_COLORS[p.name];
        const bgColor = PERSONA_BG_COLORS[p.name] || '#f4f8f5';
        return (
          <button
            key={p.name}
            onClick={() => onChange(p.name)}
            className="flex flex-col items-center gap-2 p-5 rounded-2xl border-2 transition-all duration-200 cursor-pointer text-center"
            style={{
              backgroundColor: isActive ? bgColor : '#fff',
              borderColor: isActive ? color : '#dce5e0',
              boxShadow: isActive ? `0 0 0 1px ${color}40` : 'none',
            }}
          >
            <span className="text-3xl">{meta.icon}</span>
            <span className="font-semibold text-sm" style={{ color }}>
              {meta.short}
            </span>
            <span className="text-xs text-surface-600 leading-snug">
              {meta.description}
            </span>
          </button>
        );
      })}
    </div>
  );
}
