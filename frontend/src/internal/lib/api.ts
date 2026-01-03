/**
 * Centralized STRYDA API Client
 * Fixed for Mobile Connection (No Localhost)
 */

import { Platform } from 'react-native';

// AUTOMATIC URL DETECTION
// 1. If Web: Use relative path (proxied)
// 2. If Native: Use explicit production URL
const PROD_URL = 'https://stryda-brain.preview.emergentagent.com'; 
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

export async function createProject(name: string, address?: string): Promise<Project> {
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  const targetUrl = `${baseUrl}/api/projects`;

  try {
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, address }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return data.project;
  } catch (error) {
    console.error('❌ Create Project Error:', error);
    throw error;
  }
}

export interface Thread {
  session_id: string;
  title: string;
  project_id?: string;
  project_name?: string;
  preview_text?: string;
  updated_at?: string;
}

export interface ThreadsResponse {
  ok: boolean;
  threads: Thread[];
}

export async function getThreads(): Promise<Thread[]> {
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  const targetUrl = `${baseUrl}/api/threads`;

  console.log(`🚀 Fetching threads from: ${targetUrl}`);

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

    const data: ThreadsResponse = await response.json();
    return data.threads;

  } catch (error) {
    console.error('❌ Get Threads Error:', error);
    return [];
  }
}

export interface UpdateThreadRequest {
  project_id?: string;
  title?: string;
}

export interface UpdateThreadResponse {
  ok: boolean;
  project_name?: string;
  project_id?: string;
  title?: string;
}

export async function assignThreadToProject(session_id: string, project_id: string): Promise<UpdateThreadResponse> {
  return updateThread(session_id, { project_id });
}

export async function updateThread(session_id: string, updates: UpdateThreadRequest): Promise<UpdateThreadResponse> {
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  const targetUrl = `${baseUrl}/api/threads/${session_id}`;

  console.log(`🚀 Updating thread ${session_id}`, updates);

  try {
    const response = await fetch(targetUrl, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`HTTP ${response.status}: ${errorText}`);
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('❌ Update Thread Error:', error);
    throw error;
  }
}

export async function deleteThread(session_id: string): Promise<void> {
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  const targetUrl = `${baseUrl}/api/threads/${session_id}`;

  console.log(`🗑️ DELETE REQUEST:`);
  console.log(`   Session ID: ${session_id}`);
  console.log(`   Target URL: ${targetUrl}`);
  console.log(`   Platform: ${Platform.OS}`);

  try {
    const response = await fetch(targetUrl, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`🗑️ DELETE RESPONSE: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ Delete failed: ${errorText}`);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    console.log(`✅ Thread deleted successfully`);
  } catch (error) {
    console.error('❌ Delete Thread Error:', error);
    throw error;
  }
}

export interface ThreadDetailResponse {
    ok: boolean;
    thread: Thread | null;
}

export async function getThreadDetails(session_id: string): Promise<Thread | null> {
    const baseUrl = API_BASE_URL.replace(/\/$/, "");
    const targetUrl = `${baseUrl}/api/threads/${session_id}`;
    
    try {
        const response = await fetch(targetUrl);
        if (!response.ok) return null;
        
        const data: ThreadDetailResponse = await response.json();
        return data.thread;
    } catch (e) {
        console.error("Failed to get thread details", e);
        return null;
    }
}

export interface Document {
    id: string;
    title: string;
    source: string;
}

export interface DocumentsResponse {
    ok: boolean;
    documents: Document[];
}

export async function getDocuments(): Promise<Document[]> {
    const baseUrl = API_BASE_URL.replace(/\/$/, "");
    const targetUrl = `${baseUrl}/api/documents`;
    
    try {
        const response = await fetch(targetUrl);
        if (!response.ok) throw new Error('Failed to fetch documents');
        
        const data: DocumentsResponse = await response.json();
        return data.documents;
    } catch (e) {
        console.error("Failed to get documents", e);
        return [];
    }
}
