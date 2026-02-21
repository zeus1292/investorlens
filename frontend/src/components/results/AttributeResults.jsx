import ResultCard from './ResultCard';
import { formatAttributeName } from '../../utils/format';

export default function AttributeResults({ results, personaColor, query }) {
  if (!results || results.length === 0) return null;

  const attribute = query?.attribute || 'moat_durability';

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-surface-800">
        Top Companies by{' '}
        <span style={{ color: personaColor }}>{formatAttributeName(attribute)}</span>
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
