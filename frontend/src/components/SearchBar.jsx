import { useState } from 'react';
import PersonaSelector from './PersonaSelector';
import DemoQueries from './DemoQueries';

export default function SearchBar({ personas, activePersona, onPersonaChange, onSearch, allPersonas, onAllPersonasToggle }) {
  const [query, setQuery] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  }

  function handleDemo(q) {
    setQuery(q);
    onSearch(q);
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search companies... e.g. Competitors to Snowflake"
            className="w-full px-4 py-3 rounded-xl bg-surface-800 border border-surface-700 text-surface-300 placeholder-surface-500 focus:outline-none focus:border-surface-500 focus:ring-1 focus:ring-surface-500 transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim()}
          className="px-6 py-3 rounded-xl bg-persona-value text-surface-900 font-semibold hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
        >
          Search
        </button>
      </form>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <PersonaSelector personas={personas} active={activePersona} onChange={onPersonaChange} />
        <label className="flex items-center gap-2 text-sm text-surface-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={allPersonas}
            onChange={(e) => onAllPersonasToggle(e.target.checked)}
            className="accent-persona-value"
          />
          Compare all personas
        </label>
      </div>

      <DemoQueries onSelect={handleDemo} />
    </div>
  );
}
