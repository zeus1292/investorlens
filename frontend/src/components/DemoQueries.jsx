const DEMOS = [
  'Competitors to Snowflake',
  'Compare Databricks vs Snowflake through a PE lens',
  'Best acquisition target for Google to compete with Palantir',
  'Competitors to C3 AI',
  'Compare Pinecone vs Weaviate through a VC lens',
  'Which data infrastructure companies have the strongest moats?',
];

export default function DemoQueries({ onSelect }) {
  return (
    <div className="flex flex-wrap gap-2">
      {DEMOS.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="px-3 py-1 rounded-lg text-xs text-surface-400 bg-surface-800 hover:bg-surface-700 hover:text-surface-300 transition-colors duration-150 cursor-pointer border border-surface-700"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
