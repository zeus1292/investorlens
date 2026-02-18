import { useState } from 'react';
import ScoreBreakdown from './ScoreBreakdown';
import { EDGE_COLORS, EDGE_LABELS } from '../../utils/colors';
import { formatCompositeScore } from '../../utils/format';

export default function ResultCard({ result, personaColor, rank }) {
  const [expanded, setExpanded] = useState(false);
  const { name, composite_score, score_breakdown, graph_context } = result;
  const displayRank = rank ?? result.rank;

  return (
    <div
      className="rounded-xl bg-white border border-surface-200 p-4 hover:border-surface-700 transition-colors duration-200 shadow-sm cursor-pointer"
      style={{ borderLeftWidth: '3px', borderLeftColor: personaColor }}
      onClick={() => setExpanded((v) => !v)}
    >
      {/* Always visible: rank + name + score + mini bar */}
      <div className="flex items-center gap-3">
        <span
          className="text-xl font-bold leading-none"
          style={{ color: personaColor, opacity: 0.8 }}
        >
          {displayRank}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-baseline justify-between gap-2">
            <h3 className="text-surface-800 font-semibold truncate">{name}</h3>
            <span className="text-sm font-mono text-surface-500 shrink-0">
              {formatCompositeScore(composite_score)}
            </span>
          </div>

          <div className="mt-1 h-1 rounded-full bg-surface-200 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(composite_score * 100, 100)}%`,
                backgroundColor: personaColor,
              }}
            />
          </div>
        </div>

        <span className="text-surface-400 text-xs shrink-0 ml-1">
          {expanded ? '▲' : '▼'}
        </span>
      </div>

      {/* Expanded: pie breakdown + graph context */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-surface-100 space-y-3">
          <ScoreBreakdown breakdown={score_breakdown} />

          {graph_context && graph_context.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {graph_context.map((edge, i) => {
                const edgeType = edge.type || '';
                const color = EDGE_COLORS[edgeType] || '#6b7280';
                const label = EDGE_LABELS[edgeType] || edgeType.replace(/_/g, ' ');
                const strength = edge.strength;
                return (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded text-[10px] font-medium"
                    style={{ backgroundColor: `${color}15`, color }}
                  >
                    {label}
                    {strength != null && ` ${strength}`}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
