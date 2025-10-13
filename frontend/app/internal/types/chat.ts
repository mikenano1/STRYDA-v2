/**
 * Chat system type definitions
 */

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface Citation {
  source: string;
  page: number;
  score: number;
  snippet: string;
  section?: string | null;
  clause?: string | null;
}

export interface ChatResponse {
  message: string;
  citations: Citation[];
  session_id: string;
  notes?: string[];
  timing_ms?: number;
  timestamp?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
  ts: number;
  error?: boolean;
  loading?: boolean;
}

export interface ChatSession {
  sessionId: string;
  messages: ChatMessage[];
  lastActivity: number;
}