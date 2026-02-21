import ResultCard from './ResultCard';

export default function AcquisitionResults({ results, personaColor, query }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-surface-800">
        Acquisition Targets for{' '}
        <span style={{ color: personaColor }}>{query?.acquirer || 'Acquirer'}</span>
        {query?.target_company && (
          <span className="text-surface-500 font-normal">
            {' '}to compete with {query.target_company}
          </span>
        )}
      </h2>
      <div className="columns-1 md:columns-2 gap-3">
        {results.map((r) => (
          <div key={r.company_id} className="break-inside-avoid mb-3">
            <ResultCard result={r} personaColor={personaColor} />
          </div>
        ))}
      </div>
    </div>
  );
}
