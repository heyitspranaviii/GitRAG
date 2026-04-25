import { useCallback } from 'react';
import { ingestRepo } from '../services/api';
import { useAppStore } from '../store';

export function useIngest() {
  const { setIngesting, setIngestStats, setError, setHealth } = useAppStore();

  const ingest = useCallback(async (repoPath: string) => {
    if (!repoPath.trim()) return;
    setIngesting(true);
    setError(null);
    try {
      const data = await ingestRepo(repoPath);
      setIngestStats(data.stats);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIngesting(false);
    }
  }, [setIngesting, setIngestStats, setError, setHealth]);

  return { ingest };
}
