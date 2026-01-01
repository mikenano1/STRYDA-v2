/**
 * Centralized STRYDA API Client
 * Fixed for Mobile Connection (No Localhost)
 */

import { Platform } from 'react-native';

// AUTOMATIC URL DETECTION
// 1. If Web: Use relative path (proxied)
// 2. If Native: Use explicit production URL
const PROD_URL = 'https://wind-calc.preview.emergentagent.com'; 
const API_BASE_URL = Platform.OS === 'web' ? '' : PROD_URL;

export interface Citation {
  source: string;
  page: number;
  score?: number;
  snippet?: string;
  section?: string;
  clause?: string;
  // Support both title and source keys
  title?: string; 
}

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface ChatResponse {
  message: string;
  answer?: string;
  citations: Citation[];
  session_id: string;
  intent?: string;
  model?: string;
  tokens_in?: number;
}

export async function chatAPI(request: ChatRequest): Promise<ChatResponse> {
  // Construct target URL
  // Ensure we don't have double slashes if base is empty
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  const targetUrl = `${baseUrl}/api/chat`;
  
  console.log(`🚀 STRYDA API Request to: ${targetUrl}`, {
    session: request.session_id.substring(0, 8) + '...'
  });

  try {
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
    }

    const data = await response.json();
    
    // Normalize response for frontend
    const finalResponse: ChatResponse = {
      message: data.answer || data.message || data.response || "",
      answer: data.answer,
      citations: data.citations || [],
      session_id: request.session_id,
      intent: data.intent,
      model: data.model
    };

    console.log('✅ API Success:', { 
      len: finalResponse.message.length, 
      cites: finalResponse.citations.length 
    });

    return finalResponse;

  } catch (error) {
    console.error('❌ Chat API Error:', error);
    throw error;
  }
}

// Legacy compatibility exports
export const sendChat = chatAPI;


export interface Project {
  id: string;
  name: string;
  address?: string;
  created_at?: string;
}

export interface ProjectsResponse {
  ok: boolean;
  projects: Project[];
}

export async function getProjects(): Promise<Project[]> {
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  const targetUrl = `${baseUrl}/api/projects`;

  console.log(`🚀 Fetching projects from: ${targetUrl}`);

  try {
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data: ProjectsResponse = await response.json();
    return data.projects;

  } catch (error) {
    console.error('❌ Get Projects Error:', error);
    return [];
  }
}
