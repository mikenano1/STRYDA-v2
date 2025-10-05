/**
 * Session management with AsyncStorage persistence
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChatMessage, ChatSession } from '../types/chat';

const SESSION_KEY = 'stryda_chat_session';
const MESSAGES_KEY = 'stryda_chat_messages';
const MAX_STORED_MESSAGES = 50;

export class SessionManager {
  /**
   * Generate new session ID using UUID v4
   */
  static generateSessionId(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  /**
   * Get current session ID or create new one
   */
  static async getCurrentSessionId(): Promise<string> {
    try {
      const sessionId = await AsyncStorage.getItem(SESSION_KEY);
      
      if (sessionId) {
        return sessionId;
      }
      
      // Create new session
      const newSessionId = this.generateSessionId();
      await AsyncStorage.setItem(SESSION_KEY, newSessionId);
      return newSessionId;
      
    } catch (error) {
      console.error('❌ Failed to get session ID:', error);
      // Fallback to in-memory session
      return this.generateSessionId();
    }
  }

  /**
   * Create new chat session (clear current)
   */
  static async createNewSession(): Promise<string> {
    try {
      const newSessionId = this.generateSessionId();
      await AsyncStorage.setItem(SESSION_KEY, newSessionId);
      await AsyncStorage.removeItem(MESSAGES_KEY);
      
      console.log('🆕 New chat session created:', newSessionId);
      return newSessionId;
      
    } catch (error) {
      console.error('❌ Failed to create new session:', error);
      return this.generateSessionId();
    }
  }

  /**
   * Load messages for current session
   */
  static async loadMessages(): Promise<ChatMessage[]> {
    try {
      const messagesJson = await AsyncStorage.getItem(MESSAGES_KEY);
      
      if (messagesJson) {
        const messages: ChatMessage[] = JSON.parse(messagesJson);
        console.log(`📱 Loaded ${messages.length} messages from storage`);
        return messages;
      }
      
      return [];
      
    } catch (error) {
      console.error('❌ Failed to load messages:', error);
      return [];
    }
  }

  /**
   * Save messages to storage (keep last 50 for performance)
   */
  static async saveMessages(messages: ChatMessage[]): Promise<void> {
    try {
      // Keep only last 50 messages for performance
      const messagesToSave = messages.slice(-MAX_STORED_MESSAGES);
      
      await AsyncStorage.setItem(MESSAGES_KEY, JSON.stringify(messagesToSave));
      console.log(`💾 Saved ${messagesToSave.length} messages to storage`);
      
    } catch (error) {
      console.error('❌ Failed to save messages:', error);
    }
  }

  /**
   * Get session info for debugging
   */
  static async getSessionInfo(): Promise<{ sessionId: string; messageCount: number }> {
    try {
      const sessionId = await this.getCurrentSessionId();
      const messages = await this.loadMessages();
      
      return {
        sessionId,
        messageCount: messages.length
      };
      
    } catch (error) {
      console.error('❌ Failed to get session info:', error);
      return {
        sessionId: 'unknown',
        messageCount: 0
      };
    }
  }
}