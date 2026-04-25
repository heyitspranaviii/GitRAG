import { create } from 'zustand';
import type { Message, HealthStatus, IngestStats } from '../types';

interface AppState {
  // Health
  health:       HealthStatus | null;
  setHealth:    (h: HealthStatus | null) => void;

  // Session
  sessionId:    string;
  setSessionId: (id: string) => void;

  // Messages
  messages:     Message[];
  addMessage:   (m: Message) => void;
  clearMessages:() => void;

  // Ingest
  ingestStats:  IngestStats | null;
  setIngestStats: (s: IngestStats | null) => void;

  // Loading states
  isIngesting:  boolean;
  isQuerying:   boolean;
  setIngesting: (v: boolean) => void;
  setQuerying:  (v: boolean) => void;

  // Error
  error:        string | null;
  setError:     (e: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  health:          null,
  setHealth:       (health) => set({ health }),

  sessionId:       'default',
  setSessionId:    (sessionId) => set({ sessionId }),

  messages:        [],
  addMessage:      (m) => set((s) => ({ messages: [...s.messages, m] })),
  clearMessages:   () => set({ messages: [] }),

  ingestStats:     null,
  setIngestStats:  (ingestStats) => set({ ingestStats }),

  isIngesting:     false,
  isQuerying:      false,
  setIngesting:    (isIngesting) => set({ isIngesting }),
  setQuerying:     (isQuerying)  => set({ isQuerying }),

  error:           null,
  setError:        (error) => set({ error }),
}));
