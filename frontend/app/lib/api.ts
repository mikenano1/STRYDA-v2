/**
 * API wrapper for STRYDA chat endpoints
 */

import { ChatRequest, ChatResponse } from '../types/chat';

const API_BASE = process.env.EXPO_PUBLIC_API_BASE || 'http://localhost:8001';

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

export async function postChat(request: ChatRequest): Promise<ChatResponse> {
  const startTime = Date.now();
  
  try {
    console.log('🚀 Chat request:', { session_id: request.session_id, message: request.message.substring(0, 50) + '...' });
    
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      timeout: 30000,
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new APIError(response.status, data.message || 'Request failed');
    }

    const latency = Date.now() - startTime;
    console.log(`✅ Chat response received: ${latency}ms, ${data.citations?.length || 0} citations`);
    
    // Analytics logging
    console.log('📊 Chat Analytics:', {
      latency_ms: latency,
      citations_count: data.citations?.length || 0,
      response_length: data.message?.length || 0,
      session_id: data.session_id
    });

    return data;
    
  } catch (error) {
    const latency = Date.now() - startTime;
    
    if (error instanceof APIError) {
      throw error;
    }
    
    console.error('❌ Chat request failed:', error);
    throw new APIError(0, `Network error: ${error.message}`);
  }
}

// Legacy ask endpoint for backward compatibility
export async function postAsk(query: string): Promise<{ answer: string; citation: any[] }> {
  try {
    const response = await fetch(`${API_BASE}/api/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Ask request failed:', error);
    throw error;
  }
}