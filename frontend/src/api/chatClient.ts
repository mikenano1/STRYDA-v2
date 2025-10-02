/**
 * Stub chat client for STRYDA-v2
 * Returns canned responses with fake citations
 */

export interface ChatResponse {
  answer: string;
  notes: string[];
  citation: string;
}

export class ChatClient {
  /**
   * Stub ask method - returns canned response after delay
   */
  async ask(text: string): Promise<ChatResponse> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 300));
    
    return {
      answer: 'Coming soon - this is a placeholder response for your query.',
      notes: ['demo', 'stub'],
      citation: 'NZMRM COP X.Y'
    };
  }
}

export const chatClient = new ChatClient();

// Export ask function directly for convenience
export async function ask(text: string): Promise<ChatResponse> {
  return chatClient.ask(text);
}
