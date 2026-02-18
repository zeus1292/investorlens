import { formatAttributeName } from '../../utils/format';

const PIE_COLORS = [
  '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#06b6d4', '#ef4444',
  '#f97316', '#ec4899', '#14b8a6', '#a855f7',
];

function PieChart({ entries, total, size = 64 }) {
  const r = size / 2;
  const cx = r;
  const cy = r;
  const innerR = r * 0.35;
  let cumulative = 0;

  const slices = entries.map(([attr, value], i) => {
    const fraction = value / total;
    const startAngle = cumulative * 2 * Math.PI - Math.PI / 2;
    cumulative += fraction;
    const endAngle = cumulative * 2 * Math.PI - Math.PI / 2;

    const largeArc = fraction > 0.5 ? 1 : 0;
    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);
    const ix1 = cx + innerR * Math.cos(startAngle);
    const iy1 = cy + innerR * Math.sin(startAngle);
    const ix2 = cx + innerR * Math.cos(endAngle);
    const iy2 = cy + innerR * Math.sin(endAngle);

    const d = [
      `M ${x1} ${y1}`,
      `A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`,
      `L ${ix2} ${iy2}`,
      `A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix1} ${iy1}`,
      'Z',
    ].join(' ');

    return (
      <path
        key={attr}
        d={d}
        fill={PIE_COLORS[i % PIE_COLORS.length]}
      >
        <title>{`${formatAttributeName(attr)}: ${(value * 100).toFixed(0)}%`}</title>
      </path>
    );
  });

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {slices}
    </svg>
  );
}

export default function ScoreBreakdown({ breakdown }) {
  if (!breakdown || Object.keys(breakdown).length === 0) return null;

  const entries = Object.entries(breakdown).filter(([, v]) => v != null && v > 0);
  if (entries.length === 0) return null;

  const total = entries.reduce((sum, [, v]) => sum + v, 0);

  return (
    <div className="flex items-start gap-3">
      <PieChart entries={entries} total={total} size={56} />
      <div className="flex flex-wrap gap-x-3 gap-y-1 flex-1 min-w-0">
        {entries.map(([attr, value], i) => (
          <span key={attr} className="flex items-center gap-1 text-[10px] text-surface-600">
            <span
              className="inline-block w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
            />
            {formatAttributeName(attr)}
            <span className="text-surface-500">{(value * 100).toFixed(0)}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
