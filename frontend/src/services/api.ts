import axios, { AxiosError } from 'axios';
import type { HealthStatus, IngestStats } from '../types';

const api = axios.create({
  baseURL: (import.meta as any).env.VITE_API_URL || '/api',
  timeout: 300_000,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor for centralised error handling
api.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ detail: string }>) => {
    const msg = err.response?.data?.detail ?? err.message ?? 'Unknown error';
    return Promise.reject(new Error(msg));
  }
);

export const healthCheck = () =>
  api.get<HealthStatus>('/health').then((r) => r.data);

export const ingestRepo = (repoPath: string) =>
  api.post<{ status: string; stats: IngestStats }>('/ingest', { repo_path: repoPath }).then((r) => r.data);

export const queryRepo = (query: string, sessionId = 'default') =>
  api.post<{ answer: string; session_id: string; elapsed_ms: number }>(
    '/query', { query, session_id: sessionId }
  ).then((r) => r.data);

export const clearMemory = (sessionId = 'default') =>
  api.delete(`/memory/${sessionId}`).then((r) => r.data);

export const getSessionTurns = (sessionId = 'default', lastN = 10) =>
  api.get(`/sessions/${sessionId}/turns`, { params: { last_n: lastN } }).then((r) => r.data);
