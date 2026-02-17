const BASE = '';

export async function searchQuery({ query, persona, includeExplanation = false, allPersonas = false }, signal) {
  const res = await fetch(`${BASE}/api/search`, {
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
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Search failed (${res.status})`);
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
