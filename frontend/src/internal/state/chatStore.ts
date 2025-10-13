/**
 * Zustand store for chat state management
 */

import { create } from 'zustand';
import { ChatMessage } from '../types/chat';
import { SessionManager } from '../lib/session';

interface ChatStore {
  // State
  sessionId: string;
  messages: ChatMessage[];
  isLoading: boolean;
  isInitialized: boolean;
  
  // Actions
  setSession: (sessionId: string) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  markFailed: (id: string) => void;
  clearMessages: () => void;
  initialize: () => Promise<void>;
  saveToStorage: () => Promise<void>;
  createNewSession: () => Promise<void>;
}

const useChatStore = create<ChatStore>((set, get) => ({
  // Initial state
  sessionId: '',
  messages: [],
  isLoading: false,
  isInitialized: false,

  // Actions
  setSession: (sessionId: string) => {
    set({ sessionId });
  },

  addMessage: (message: ChatMessage) => {
    const { messages } = get();
    const newMessages = [...messages, message];
    
    set({ messages: newMessages });
    
    // Auto-save to storage (debounced in practice)
    get().saveToStorage();
  },

  updateMessage: (id: string, updates: Partial<ChatMessage>) => {
    const { messages } = get();
    const newMessages = messages.map(msg => 
      msg.id === id ? { ...msg, ...updates } : msg
    );
    
    set({ messages: newMessages });
    get().saveToStorage();
  },

  markFailed: (id: string) => {
    get().updateMessage(id, { error: true, loading: false });
  },

  clearMessages: () => {
    set({ messages: [] });
    get().saveToStorage();
  },

  initialize: async () => {
    try {
      set({ isLoading: true });
      
      // Get or create session ID
      const sessionId = await SessionManager.getCurrentSessionId();
      
      // Load persisted messages
      const messages = await SessionManager.loadMessages();
      
      set({ 
        sessionId,
        messages,
        isLoading: false,
        isInitialized: true 
      });
      
      console.log('🔄 Chat store initialized:', { sessionId, messageCount: messages.length });
      
    } catch (error) {
      console.error('❌ Chat store initialization failed:', error);
      set({ 
        sessionId: SessionManager.generateSessionId(),
        messages: [],
        isLoading: false,
        isInitialized: true 
      });
    }
  },

  saveToStorage: async () => {
    try {
      const { messages } = get();
      await SessionManager.saveMessages(messages);
    } catch (error) {
      console.error('❌ Failed to save messages:', error);
    }
  },

  createNewSession: async () => {
    try {
      const newSessionId = await SessionManager.createNewSession();
      
      set({ 
        sessionId: newSessionId,
        messages: [],
      });
      
      console.log('🆕 New chat session started:', newSessionId);
      
    } catch (error) {
      console.error('❌ Failed to create new session:', error);
    }
  }
}));

// Utility selectors
export const useChatMessages = () => useChatStore(state => state.messages);
export const useSessionId = () => useChatStore(state => state.sessionId);
export const useIsLoading = () => useChatStore(state => state.isLoading);
export const useIsInitialized = () => useChatStore(state => state.isInitialized);

// Action selectors
export const useChatActions = () => useChatStore(state => ({
  addMessage: state.addMessage,
  updateMessage: state.updateMessage,
  markFailed: state.markFailed,
  clearMessages: state.clearMessages,
  initialize: state.initialize,
  createNewSession: state.createNewSession
}));

export default useChatStore;