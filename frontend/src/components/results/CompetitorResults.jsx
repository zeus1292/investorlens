import ResultCard from './ResultCard';

export default function CompetitorResults({ results, personaColor, targetCompany }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="space-y-3">
      {targetCompany && (
        <h2 className="text-lg font-semibold text-white">
          Competitors to <span style={{ color: personaColor }}>{targetCompany}</span>
        </h2>
      )}
      {results.map((r) => (
        <ResultCard key={r.company_id} result={r} personaColor={personaColor} />
      ))}
    </div>
  );
}
