const BASE = import.meta.env.VITE_API_URL || '';

export async function searchQuery({ query, persona, includeExplanation = false, allPersonas = false }, signal) {
  let res;
  try {
    res = await fetch(`${BASE}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        persona,
        include_explanation: includeExplanation,
        all_personas: allPersonas,
      }),
      signal,
    });
  } catch (e) {
    if (e.name === 'AbortError') throw e;
    throw new Error('Unable to reach the server. It may still be starting up — please wait a moment and try again.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: null }));
    throw new Error(err.detail || 'Something went wrong. Please try your search again.');
  }
  return res.json();
}

export async function fetchPersonas() {
  const res = await fetch(`${BASE}/api/personas`);
  if (!res.ok) throw new Error('Failed to fetch personas');
  return res.json();
}

export async function fetchCompanies() {
  const res = await fetch(`${BASE}/api/companies`);
  if (!res.ok) throw new Error('Failed to fetch companies');
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}
