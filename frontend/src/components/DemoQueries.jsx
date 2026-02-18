const PERSONA_QUERIES = {
  value_investor: [
    'Competitors to Snowflake',
    'Which data infrastructure companies have the strongest moats?',
    'Compare Databricks vs Snowflake',
  ],
  pe_firm: [
    'Compare Databricks vs Snowflake through a PE lens',
    'Competitors to Snowflake',
    'Which companies have the highest margins?',
  ],
  growth_vc: [
    'Competitors to C3 AI',
    'Compare Pinecone vs Weaviate through a VC lens',
    'Which companies have the strongest developer adoption?',
  ],
  strategic_acquirer: [
    'Best acquisition target for Google to compete with Palantir',
    'Competitors to Snowflake',
    'Best acquisition target for Databricks',
  ],
  enterprise_buyer: [
    'Competitors to Snowflake',
    'Compare Databricks vs Snowflake',
    'Which companies have the strongest enterprise readiness?',
  ],
};

export default function DemoQueries({ onSelect, persona }) {
  const queries = PERSONA_QUERIES[persona] || PERSONA_QUERIES.value_investor;

  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {queries.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="px-4 py-2 rounded-xl text-sm text-surface-600 bg-white hover:bg-surface-100 hover:text-surface-800 transition-colors duration-150 cursor-pointer border border-surface-200 shadow-sm"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
