import { useState, useEffect } from 'react';
import { fetchCompanies } from '../api/client';

export function useCompanies() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchCompanies()
      .then((data) => { if (!cancelled) setCompanies(data); })
      .catch((e) => console.warn('Failed to load companies:', e.message))
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return { companies, loading };
}
