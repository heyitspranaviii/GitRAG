import { useEffect, useCallback } from 'react';
import { healthCheck } from '../services/api';
import { useAppStore } from '../store';

export function useHealth() {
  const setHealth = useAppStore((s) => s.setHealth);

  const check = useCallback(async () => {
    try {
      const data = await healthCheck();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  }, [setHealth]);

  useEffect(() => {
    check();
    const interval = setInterval(check, 30_000);
    return () => clearInterval(interval);
  }, [check]);
}
