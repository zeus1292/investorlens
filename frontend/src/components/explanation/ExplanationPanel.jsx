export default function ExplanationPanel({ explanation, highlights, loading }) {
  return (
    <div className="rounded-xl bg-surface-800 border border-surface-700 p-4">
      <h3 className="text-sm font-medium text-surface-400 mb-3">Analysis</h3>

      {loading && !explanation && (
        <div className="space-y-2 animate-pulse">
          <div className="h-3 bg-surface-700 rounded w-full" />
          <div className="h-3 bg-surface-700 rounded w-5/6" />
          <div className="h-3 bg-surface-700 rounded w-4/6" />
          <div className="h-3 bg-surface-700 rounded w-full" />
          <div className="h-3 bg-surface-700 rounded w-3/6" />
          <p className="text-xs text-surface-500 mt-3">Generating analysis...</p>
        </div>
      )}

      {explanation && (
        <div className="space-y-3">
          <p className="text-sm text-surface-300 leading-relaxed whitespace-pre-line">{explanation}</p>

          {highlights && highlights.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-surface-700">
              <span className="text-xs font-medium text-surface-500">Key Insights</span>
              <ul className="space-y-1">
                {highlights.map((h, i) => (
                  <li key={i} className="text-xs text-surface-400 flex gap-2">
                    <span className="text-persona-value shrink-0">-</span>
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!loading && !explanation && (
        <p className="text-xs text-surface-500">
          Analysis will appear here after search results load.
        </p>
      )}
    </div>
  );
}
