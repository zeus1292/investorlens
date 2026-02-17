import { useState, useCallback } from 'react';
import SearchBar from './components/SearchBar';
import LoadingSpinner from './components/common/LoadingSpinner';
import ErrorBanner from './components/common/ErrorBanner';
import MetadataBar from './components/common/MetadataBar';
import ResultsContainer from './components/results/ResultsContainer';
import GraphPanel from './components/graph/GraphPanel';
import ExplanationPanel from './components/explanation/ExplanationPanel';
import CrossPersonaTable from './components/crossPersona/CrossPersonaTable';
import { useSearch } from './hooks/useSearch';
import { usePersonas } from './hooks/usePersonas';

const DEFAULT_PERSONA = 'value_investor';

function WelcomeState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <h2 className="text-3xl font-bold text-white mb-2">InvestorLens</h2>
      <p className="text-surface-400 max-w-lg mb-6">
        Persona-driven company intelligence for Enterprise AI &amp; Data Infrastructure.
        The same query returns different results depending on who&apos;s asking.
      </p>
      <p className="text-xs text-surface-500">
        Try a demo query above, or type your own search.
      </p>
    </div>
  );
}

export default function App() {
  const [persona, setPersona] = useState(DEFAULT_PERSONA);
  const [allPersonasMode, setAllPersonasMode] = useState(false);
  const { personas } = usePersonas();
  const {
    results,
    explanation,
    explanationHighlights,
    loading,
    explanationLoading,
    error,
    search,
    clear,
  } = useSearch();

  const handleSearch = useCallback(
    (query) => {
      search(query, persona, allPersonasMode);
    },
    [search, persona, allPersonasMode],
  );

  const handlePersonaChange = useCallback(
    (newPersona) => {
      setPersona(newPersona);
      // Re-run current query with new persona if we have results
      if (results?.query?.raw_query) {
        search(results.query.raw_query, newPersona, allPersonasMode);
      }
    },
    [search, results, allPersonasMode],
  );

  const handleAllPersonasToggle = useCallback(
    (checked) => {
      setAllPersonasMode(checked);
      if (results?.query?.raw_query) {
        search(results.query.raw_query, persona, checked);
      }
    },
    [search, results, persona],
  );

  const hasResults = results && results.results && results.results.length > 0;

  return (
    <div className="min-h-screen bg-surface-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-surface-900/95 backdrop-blur border-b border-surface-800">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <SearchBar
            personas={personas}
            activePersona={persona}
            onPersonaChange={handlePersonaChange}
            onSearch={handleSearch}
            allPersonas={allPersonasMode}
            onAllPersonasToggle={handleAllPersonasToggle}
          />
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <ErrorBanner message={error} onDismiss={clear} />

        {loading && <LoadingSpinner />}

        {!loading && !hasResults && !error && <WelcomeState />}

        {hasResults && (
          <>
            <MetadataBar
              metadata={results.metadata}
              persona={results.persona_display}
              resultCount={results.results.length}
            />

            <div className="mt-4 grid grid-cols-1 lg:grid-cols-5 gap-6">
              {/* Left column: results */}
              <div className="lg:col-span-3">
                <ResultsContainer data={results} />
              </div>

              {/* Right column: graph + explanation */}
              <div className="lg:col-span-2 space-y-4 lg:sticky lg:top-32 lg:self-start">
                <GraphPanel graphData={results.graph_data} />
                <ExplanationPanel
                  explanation={explanation}
                  highlights={explanationHighlights}
                  loading={explanationLoading}
                />
              </div>
            </div>

            {/* Cross-persona comparison */}
            {results.all_personas && (
              <div className="mt-6">
                <CrossPersonaTable
                  allPersonas={results.all_personas}
                  activePersona={persona}
                />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
