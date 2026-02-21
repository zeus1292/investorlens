import ResultCard from './ResultCard';

export default function CompetitorResults({ results, personaColor, targetCompany }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="space-y-3">
      {targetCompany && (
        <h2 className="text-lg font-semibold text-surface-800">
          Competitors to <span style={{ color: personaColor }}>{targetCompany}</span>
        </h2>
      )}
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
