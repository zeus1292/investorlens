import { useState, useEffect } from 'react';
import { fetchPersonas } from '../api/client';

export function usePersonas() {
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchPersonas()
      .then((data) => { if (!cancelled) setPersonas(data); })
      .catch((e) => console.warn('Failed to load personas:', e.message))
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return { personas, loading };
}
