import { useState } from 'react';
import PersonaSelector from './PersonaSelector';
import DemoQueries from './DemoQueries';

export default function SearchBar({ personas, activePersona, onPersonaChange, onSearch, allPersonas, onAllPersonasToggle, mode = 'landing' }) {
  const [query, setQuery] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  }

  function handleDemo(q) {
    setQuery(q);
    onSearch(q);
  }

  if (mode === 'header') {
    return (
      <div className="flex items-center gap-4">
        <PersonaSelector personas={personas} active={activePersona} onChange={onPersonaChange} compact />
        <form onSubmit={handleSubmit} className="flex-1 flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search companies..."
            className="flex-1 px-4 py-2 rounded-xl bg-white border border-surface-200 text-surface-800 placeholder-surface-500 focus:outline-none focus:border-persona-value focus:ring-1 focus:ring-persona-value transition-colors text-sm"
          />
          <button
            type="submit"
            disabled={!query.trim()}
            className="px-5 py-2 rounded-xl bg-persona-value text-white font-semibold text-sm hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
          >
            Search
          </button>
        </form>
        <label className="flex items-center gap-2 text-xs text-surface-600 cursor-pointer select-none whitespace-nowrap">
          <input
            type="checkbox"
            checked={allPersonas}
            onChange={(e) => onAllPersonasToggle(e.target.checked)}
            className="accent-persona-value"
          />
          All personas
        </label>
      </div>
    );
  }

  // Landing mode
  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search companies... e.g. Competitors to Snowflake"
            className="w-full px-5 py-3.5 rounded-2xl bg-white border border-surface-200 text-surface-800 placeholder-surface-500 focus:outline-none focus:border-persona-value focus:ring-1 focus:ring-persona-value transition-colors shadow-sm"
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim()}
          className="px-6 py-3.5 rounded-2xl bg-persona-value text-white font-semibold hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer shadow-sm"
        >
          Search
        </button>
      </form>

      <div className="flex justify-center">
        <label className="flex items-center gap-2 text-sm text-surface-600 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={allPersonas}
            onChange={(e) => onAllPersonasToggle(e.target.checked)}
            className="accent-persona-value"
          />
          Compare all personas
        </label>
      </div>

      <DemoQueries onSelect={handleDemo} persona={activePersona} />
    </div>
  );
}
