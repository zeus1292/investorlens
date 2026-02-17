import { PERSONA_COLORS } from '../utils/colors';

const PERSONA_META = {
  value_investor: { icon: '🏛', short: 'Value' },
  pe_firm: { icon: '🏢', short: 'PE' },
  growth_vc: { icon: '🚀', short: 'VC' },
  strategic_acquirer: { icon: '🎯', short: 'Acquirer' },
  enterprise_buyer: { icon: '🏗', short: 'Buyer' },
};

export default function PersonaSelector({ personas, active, onChange }) {
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
              color: isActive ? '#111827' : color,
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
