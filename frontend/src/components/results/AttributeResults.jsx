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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {results.map((r) => (
          <ResultCard key={r.company_id} result={r} personaColor={personaColor} />
        ))}
      </div>
    </div>
  );
}
