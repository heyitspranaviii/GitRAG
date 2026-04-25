export interface Message {
  id:        string;
  role:      'user' | 'assistant';
  content:   string;
  timestamp: Date;
  elapsed_ms?: number;
}

export interface IngestStats {
  files:     number;
  chunks:    number;
  findings:  number;
  elapsed_s: number;
}

export interface HealthStatus {
  status:     string;
  ready:      boolean;
  model:      string;
  index_size: number;
}

export interface Session {
  id:       string;
  messages: Message[];
}
