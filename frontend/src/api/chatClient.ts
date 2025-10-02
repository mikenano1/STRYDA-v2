import { config } from './config';
import { postJSON, HttpError } from './httpClient';
import { Alert, Platform } from 'react-native';

export interface ChatResponse {
  answer: string;
  notes: string[];
  citation: string;
}

/**
 * Stub response - used as fallback when backend is unavailable
 */
function getStubResponse(): ChatResponse {
  return {
    answer: 'Coming soon - this is a placeholder response (fallback mode).',
    notes: ['demo', 'stub', 'fallback'],
    citation: 'NZMRM COP X.Y'
  };
}

/**
 * Show toast/alert for fallback
 */
function showFallbackMessage() {
  if (Platform.OS === 'web') {
    // Simple notification for web
    console.warn('⚠️ Backend unavailable, using fallback');
  } else {
    Alert.alert(
      'Temporary Issue',
      'Using fallback mode. Backend is temporarily unavailable.',
      [{ text: 'OK' }]
    );
  }
}

/**
 * Ask a question - tries backend first, falls back to stub
 */
export async function ask(query: string): Promise<ChatResponse> {
  // If backend is disabled, use stub immediately
  if (!config.USE_BACKEND) {
    console.log('📍 Using stub client (backend disabled)');
    await new Promise(resolve => setTimeout(resolve, 300)); // Simulate delay
    return getStubResponse();
  }

  // Try backend
  try {
    console.log('🚀 Calling backend:', `${config.API_BASE}/api/ask`);
    const response = await postJSON<ChatResponse>(
      `${config.API_BASE}/api/ask`,
      { query },
      10000 // 10s timeout
    );
    console.log('✅ Backend response received');
    return response;
  } catch (error) {
    const httpError = error as HttpError;
    console.error('❌ Backend error:', httpError.message);

    // Show user-friendly message
    showFallbackMessage();

    // Use stub as fallback
    await new Promise(resolve => setTimeout(resolve, 300));
    return getStubResponse();
  }
}
