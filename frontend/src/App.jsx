import { useState, useCallback, useEffect } from 'react';
import SearchBar from './components/SearchBar';
import PersonaSelector from './components/PersonaSelector';
import LoadingSpinner from './components/common/LoadingSpinner';
import ErrorBanner from './components/common/ErrorBanner';
import MetadataBar from './components/common/MetadataBar';
import ResultsContainer from './components/results/ResultsContainer';
import GraphPanel from './components/graph/GraphPanel';
import ExplanationPanel from './components/explanation/ExplanationPanel';
import CrossPersonaTable from './components/crossPersona/CrossPersonaTable';
import { useSearch } from './hooks/useSearch';
import { usePersonas } from './hooks/usePersonas';
import { fetchHealth } from './api/client';

const DEFAULT_PERSONA = 'value_investor';

function DataSnapshot() {
  const stats = [
    { label: 'Companies', value: '37' },
    { label: 'Sectors', value: '6' },
    { label: 'Relationships', value: '384' },
    { label: 'Personas', value: '5' },
  ];
  return (
    <div className="flex justify-center gap-8">
      {stats.map((s) => (
        <div key={s.label} className="text-center">
          <div className="text-2xl font-bold text-persona-value">{s.value}</div>
          <div className="text-xs text-surface-600">{s.label}</div>
        </div>
      ))}
    </div>
  );
}

const TABS = [
  { id: 'rankings', label: 'Rankings' },
  { id: 'relationship-map', label: 'Relationship Map' },
];

export default function App() {
  const [persona, setPersona] = useState(DEFAULT_PERSONA);
  const [allPersonasMode, setAllPersonasMode] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [activeTab, setActiveTab] = useState('rankings');
  const [showWarmingBanner, setShowWarmingBanner] = useState(false);

  // Ping health on mount — show warming banner only if server takes > 2s
  useEffect(() => {
    let timer;
    let resolved = false;

    timer = setTimeout(() => {
      if (!resolved) setShowWarmingBanner(true);
    }, 2000);

    fetchHealth()
      .then(() => {
        resolved = true;
        clearTimeout(timer);
        setShowWarmingBanner(false);
      })
      .catch(() => {
        resolved = true;
        clearTimeout(timer);
        setShowWarmingBanner(false);
      });

    return () => { resolved = true; clearTimeout(timer); };
  }, []);
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
      setHasSearched(true);
      setActiveTab('rankings');
      search(query, persona, allPersonasMode);
    },
    [search, persona, allPersonasMode],
  );

  const handlePersonaChange = useCallback(
    (newPersona) => {
      setPersona(newPersona);
      if (hasSearched && results?.query?.raw_query) {
        search(results.query.raw_query, newPersona, allPersonasMode);
      }
    },
    [search, results, allPersonasMode, hasSearched],
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

  const handleBackToLanding = useCallback(() => {
    setHasSearched(false);
    clear();
  }, [clear]);

  const handleNodeClick = useCallback((companyLabel) => {
    setActiveTab('rankings');
    handleSearch(`Competitors to ${companyLabel}`);
  }, [handleSearch]);

  const hasResults = results && results.results && results.results.length > 0;

  const WarmingBanner = showWarmingBanner ? (
    <div className="w-full bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-xs text-amber-800">
      Server is starting up — first search may take up to 30 seconds. Hang tight.
    </div>
  ) : null;

  // Landing view
  if (!hasSearched && !loading) {
    return (
      <div className="min-h-screen bg-surface-50 flex flex-col">
        {WarmingBanner}
        <div className="flex-1 flex flex-col items-center justify-center px-4">
        <div className="w-full max-w-3xl space-y-10 text-center">
          {/* Title */}
          <div className="space-y-3">
            <h1 className="text-4xl font-bold text-surface-900">InvestorLens</h1>
            <p className="text-surface-600 max-w-lg mx-auto">
              Persona-driven company intelligence for Enterprise AI &amp; Data Infrastructure.
              The same query returns different results depending on who&apos;s asking.
            </p>
          </div>

          {/* Data snapshot */}
          <DataSnapshot />

          {/* Pick your lens */}
          <div className="space-y-4">
            <h2 className="text-sm font-semibold text-surface-500 uppercase tracking-wider">
              Pick your lens
            </h2>
            <PersonaSelector
              personas={personas}
              active={persona}
              onChange={setPersona}
            />
          </div>

          {/* Search bar + demo queries */}
          <SearchBar
            personas={personas}
            activePersona={persona}
            onPersonaChange={setPersona}
            onSearch={handleSearch}
            allPersonas={allPersonasMode}
            onAllPersonasToggle={setAllPersonasMode}
            mode="landing"
          />
        </div>
        </div>
      </div>
    );
  }

  // Results view
  return (
    <div className="min-h-screen bg-surface-50">
      {WarmingBanner}
      {/* Compact header */}
      <header className="sticky top-0 z-50 bg-surface-50/95 backdrop-blur border-b border-surface-200">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center gap-4">
            <button
              onClick={handleBackToLanding}
              className="text-lg font-bold text-persona-value hover:opacity-80 transition-opacity cursor-pointer whitespace-nowrap"
            >
              InvestorLens
            </button>
            <div className="flex-1">
              <SearchBar
                personas={personas}
                activePersona={persona}
                onPersonaChange={handlePersonaChange}
                onSearch={handleSearch}
                allPersonas={allPersonasMode}
                onAllPersonasToggle={handleAllPersonasToggle}
                mode="header"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <ErrorBanner message={error} onDismiss={clear} />

        {loading && <LoadingSpinner />}

        {hasResults && (
          <>
            <MetadataBar
              metadata={results.metadata}
              persona={results.persona_display}
              resultCount={results.results.length}
            />

            {/* Tab bar */}
            <div className="mt-4 flex gap-0 border-b border-surface-200">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={[
                    'px-4 py-2 text-sm font-medium transition-colors -mb-px border-b-2',
                    activeTab === tab.id
                      ? 'text-surface-900 border-persona-value'
                      : 'text-surface-400 border-transparent hover:text-surface-600',
                  ].join(' ')}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="mt-5 space-y-6">
              {activeTab === 'rankings' && (
                <>
                  <ResultsContainer data={results} />
                  <ExplanationPanel
                    explanation={explanation}
                    highlights={explanationHighlights}
                    loading={explanationLoading}
                  />
                </>
              )}

              {activeTab === 'relationship-map' && (
                <GraphPanel graphData={results.graph_data} height={620} onNodeClick={handleNodeClick} />
              )}
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
