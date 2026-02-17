import ScoreBreakdown from './ScoreBreakdown';
import { EDGE_COLORS, EDGE_LABELS } from '../../utils/colors';
import { formatCompositeScore } from '../../utils/format';

export default function ResultCard({ result, personaColor, rank }) {
  const { name, composite_score, score_breakdown, graph_context } = result;
  const displayRank = rank ?? result.rank;

  return (
    <div
      className="rounded-xl bg-surface-800 border border-surface-700 p-4 hover:border-surface-600 transition-colors duration-200"
      style={{ borderLeftWidth: '3px', borderLeftColor: personaColor }}
    >
      <div className="flex items-start gap-3 mb-3">
        {/* Rank */}
        <span
          className="text-2xl font-bold leading-none mt-0.5"
          style={{ color: personaColor, opacity: 0.8 }}
        >
          {displayRank}
        </span>

        <div className="flex-1 min-w-0">
          {/* Name + score */}
          <div className="flex items-baseline justify-between gap-2">
            <h3 className="text-white font-semibold truncate">{name}</h3>
            <span className="text-sm font-mono text-surface-400 shrink-0">
              {formatCompositeScore(composite_score)}
            </span>
          </div>

          {/* Score bar */}
          <div className="mt-1 h-1 rounded-full bg-surface-700 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(composite_score * 100, 100)}%`,
                backgroundColor: personaColor,
              }}
            />
          </div>
        </div>
      </div>

      {/* Score breakdown */}
      <ScoreBreakdown breakdown={score_breakdown} />

      {/* Graph context badges */}
      {graph_context && graph_context.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {graph_context.map((edge, i) => {
            const edgeType = edge.type || '';
            const color = EDGE_COLORS[edgeType] || '#6b7280';
            const label = EDGE_LABELS[edgeType] || edgeType.replace(/_/g, ' ');
            const strength = edge.strength;
            return (
              <span
                key={i}
                className="px-2 py-0.5 rounded text-[10px] font-medium"
                style={{ backgroundColor: `${color}20`, color }}
              >
                {label}
                {strength != null && ` ${strength}`}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
