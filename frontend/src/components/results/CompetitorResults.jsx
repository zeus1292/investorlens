import ResultCard from './ResultCard';
import CompanyLogo from '../common/CompanyLogo';

export default function CompetitorResults({ results, personaColor, targetCompany, targetCompanyId }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="space-y-3">
      {targetCompany && (
        <div className="flex items-center gap-2.5">
          <CompanyLogo companyId={targetCompanyId} name={targetCompany} size={32} />
          <h2 className="text-lg font-semibold text-surface-800">
            Competitors to <span style={{ color: personaColor }}>{targetCompany}</span>
          </h2>
        </div>
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
