import ResultCard from './ResultCard';

export default function AcquisitionResults({ results, personaColor, query }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-white">
        Acquisition Targets for{' '}
        <span style={{ color: personaColor }}>{query?.acquirer || 'Acquirer'}</span>
        {query?.target_company && (
          <span className="text-surface-400 font-normal">
            {' '}to compete with {query.target_company}
          </span>
        )}
      </h2>
      {results.map((r) => (
        <ResultCard key={r.company_id} result={r} personaColor={personaColor} />
      ))}
    </div>
  );
}
