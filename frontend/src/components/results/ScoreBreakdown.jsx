import { formatAttributeName } from '../../utils/format';

const BAR_COLORS = [
  '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#06b6d4', '#ef4444',
  '#f97316', '#ec4899', '#14b8a6', '#a855f7',
];

export default function ScoreBreakdown({ breakdown, compact = false }) {
  if (!breakdown || Object.keys(breakdown).length === 0) return null;

  const entries = Object.entries(breakdown).filter(([, v]) => v != null && v > 0);
  if (entries.length === 0) return null;

  const total = entries.reduce((sum, [, v]) => sum + v, 0);

  return (
    <div className={compact ? 'space-y-1' : 'space-y-2'}>
      {/* Stacked horizontal bar */}
      <div className="flex h-2 rounded-full overflow-hidden bg-surface-700">
        {entries.map(([attr, value], i) => (
          <div
            key={attr}
            title={`${formatAttributeName(attr)}: ${(value * 100).toFixed(0)}%`}
            style={{
              width: `${(value / total) * 100}%`,
              backgroundColor: BAR_COLORS[i % BAR_COLORS.length],
            }}
          />
        ))}
      </div>

      {/* Legend */}
      {!compact && (
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          {entries.map(([attr, value], i) => (
            <span key={attr} className="flex items-center gap-1 text-[10px] text-surface-400">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: BAR_COLORS[i % BAR_COLORS.length] }}
              />
              {formatAttributeName(attr)}
              <span className="text-surface-500">{(value * 100).toFixed(0)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
