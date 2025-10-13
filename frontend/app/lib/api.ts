/**
 * Centralized STRYDA API Client
 * All chat requests go through this single endpoint
 */

import { API_BASE } from '../config/constants';

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface Citation {
  source: string;
  page: number;
  score?: number;
  snippet?: string;
  section?: string;
  clause?: string;
}

export interface ChatResponse {
  message: string;
  citations: Citation[];
  session_id: string;
  intent?: string;
  confidence?: number;
  notes?: string[];
  timing_ms?: number;
}

export async function chatAPI(request: ChatRequest): Promise<ChatResponse> {
  console.log('🚀 STRYDA API Request:', { 
    endpoint: `${API_BASE}/api/chat`,
    session_id: request.session_id.substring(0, 8) + '...',
    message_length: request.message.length 
  });
  
  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${response.statusText}. ${errorText.substring(0, 120)}`);
    }

    const data = await response.json();
    
    console.log('✅ STRYDA API Response:', {
      message_length: data.message?.length,
      citations_count: data.citations?.length,
      intent: data.intent,
      timing_ms: data.timing_ms
    });

    return data;
    
  } catch (error) {
    console.error('❌ STRYDA API Error:', error);
    throw error;
  }
}

// Legacy compatibility
export const sendChat = chatAPI;
export const postChat = chatAPI;