import { useState, useRef, useCallback } from 'react';
import { searchQuery } from '../api/client';

export function useSearch() {
  const [results, setResults] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [explanationHighlights, setExplanationHighlights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const search = useCallback(async (query, persona, allPersonas = false) => {
    // Cancel any in-flight requests
    if (abortRef.current) abortRef.current.abort();

    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    setResults(null);
    setExplanation(null);
    setExplanationHighlights(null);

    try {
      // Phase 1: fast structural results (no explanation)
      const fast = await searchQuery(
        { query, persona, includeExplanation: false, allPersonas },
        controller.signal,
      );
      setResults(fast);
      setLoading(false);

      // Phase 2: fetch explanation in background
      setExplanationLoading(true);
      try {
        const full = await searchQuery(
          { query, persona, includeExplanation: true, allPersonas },
          controller.signal,
        );
        setExplanation(full.explanation);
        setExplanationHighlights(full.explanation_highlights);
      } catch (e) {
        if (e.name !== 'AbortError') {
          console.warn('Explanation fetch failed:', e.message);
        }
      } finally {
        setExplanationLoading(false);
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        setError(e.message);
        setLoading(false);
      }
    }
  }, []);

  const clear = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    setResults(null);
    setExplanation(null);
    setExplanationHighlights(null);
    setError(null);
    setLoading(false);
    setExplanationLoading(false);
  }, []);

  return {
    results,
    explanation,
    explanationHighlights,
    loading,
    explanationLoading,
    error,
    search,
    clear,
  };
}
