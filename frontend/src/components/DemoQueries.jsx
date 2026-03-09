const PERSONA_QUERIES = {
  value_investor: [
    { type: 'Competitors', query: 'Competitors to Snowflake' },
    { type: 'Compare',     query: 'Compare Palantir vs C3 AI' },
    { type: 'Acquisition', query: 'Best acquisition target for Databricks' },
    { type: 'Ranking',     query: 'Which data infrastructure companies have the strongest moats?' },
  ],
  pe_firm: [
    { type: 'Competitors', query: 'Competitors to Informatica' },
    { type: 'Compare',     query: 'Compare Databricks vs Snowflake through a PE lens' },
    { type: 'Acquisition', query: 'Best acquisition target for Google to compete with Palantir' },
    { type: 'Ranking',     query: 'Which companies have the highest revenue predictability?' },
  ],
  growth_vc: [
    { type: 'Competitors', query: 'Competitors to C3 AI' },
    { type: 'Compare',     query: 'Compare Pinecone vs Weaviate through a VC lens' },
    { type: 'Acquisition', query: 'Best acquisition target for Databricks to compete with Snowflake' },
    { type: 'Ranking',     query: 'Which companies have the strongest developer adoption?' },
  ],
  strategic_acquirer: [
    { type: 'Competitors', query: 'Competitors to Palantir' },
    { type: 'Compare',     query: 'Compare Databricks vs Snowflake' },
    { type: 'Acquisition', query: 'Best acquisition target for Google to compete with Palantir' },
    { type: 'Ranking',     query: 'Which companies have the best integration ecosystem?' },
  ],
  enterprise_buyer: [
    { type: 'Competitors', query: 'Competitors to Snowflake' },
    { type: 'Compare',     query: 'Compare Databricks vs Snowflake' },
    { type: 'Acquisition', query: 'Best acquisition target for Databricks' },
    { type: 'Ranking',     query: 'Which companies have the strongest enterprise readiness?' },
  ],
};

const TYPE_STYLES = {
  Competitors: 'bg-blue-50 text-blue-600',
  Compare:     'bg-purple-50 text-purple-600',
  Acquisition: 'bg-amber-50 text-amber-600',
  Ranking:     'bg-emerald-50 text-emerald-600',
};

export default function DemoQueries({ onSelect, persona }) {
  const queries = PERSONA_QUERIES[persona] || PERSONA_QUERIES.value_investor;

  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {queries.map(({ type, query }) => (
        <button
          key={query}
          onClick={() => onSelect(query)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-surface-600 bg-white hover:bg-surface-100 hover:text-surface-800 transition-colors duration-150 cursor-pointer border border-surface-200 shadow-sm text-left"
        >
          <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-md shrink-0 ${TYPE_STYLES[type]}`}>
            {type}
          </span>
          {query}
        </button>
      ))}
    </div>
  );
}
