/**
 * Chat system type definitions
 */

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface EvidenceItem {
  text: string;
  page?: string;
  clause?: string;
  section?: string;
  score?: number;
  doc_type?: string;
  original_source?: string;
}

export interface Citation {
  id?: string;
  source: string;
  title?: string;
  page?: number;
  pages?: string;
  score?: number;
  snippet?: string;
  text_content?: string;  // Full RAG snippet for Evidence Modal
  evidence_collection?: EvidenceItem[];  // Multi-evidence support
  section?: string | null;
  clause?: string | null;
  confidence?: number;
  doc_count?: number;
  pill_text?: string;
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