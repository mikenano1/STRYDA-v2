import { makeAutoObservable } from "mobx";
import { sendChat } from "../lib/api/chat";
import { getSessionId, clearSession } from "../lib/session";
import AsyncStorage from "@react-native-async-storage/async-storage";

export type ChatMsg = { 
  id: string;
  role: "user"|"assistant"; 
  text: string; 
  citations?: any[]; 
  createdAt: number;
  timing_ms?: number;
  error?: boolean;
};

class ChatStore {
  messages: ChatMsg[] = [];
  loading = false;
  lastError: string | null = null;
  sessionId: string = "";
  requestCounter = 0;

  constructor(){ 
    makeAutoObservable(this);
  }

  async bootstrap() {
    try {
      this.sessionId = await getSessionId();
      await this.loadMessages();
      console.log('🔄 Chat store bootstrapped:', { 
        sessionId: this.sessionId.substring(0, 8) + '...',
        messageCount: this.messages.length 
      });
    } catch (error) {
      console.error('❌ Bootstrap failed:', error);
    }
  }

  async send(text: string) {
    if (this.loading || !text.trim()) return;
    
    this.lastError = null;
    this.requestCounter++;
    const requestId = `req_${this.requestCounter}`;
    
    // Add user message
    const userMsg: ChatMsg = {
      id: `${Date.now()}_user`,
      role: "user",
      text: text.trim(),
      createdAt: Date.now()
    };
    
    this.messages.push(userMsg);
    this.loading = true;
    
    // Telemetry: request started
    console.log(`[telemetry] chat_send ${requestId} len=${text.length}`);
    
    const t0 = performance.now();
    
    try {
      const res = await sendChat(this.sessionId, text.trim());
      const duration = performance.now() - t0;
      
      // Add assistant message
      const assistantMsg: ChatMsg = {
        id: `${Date.now()}_assistant`,
        role: "assistant",
        text: res.message,
        citations: res.citations,
        createdAt: Date.now(),
        timing_ms: res.timing_ms
      };
      
      this.messages.push(assistantMsg);
      
      // Telemetry: request succeeded
      console.log(`[telemetry] chat_response ${requestId} timing_ms=${Math.round(duration)} citations_count=${res.citations?.length || 0}`);
      
      // Persist messages
      await this.saveMessages();
      
    } catch (e: any) {
      const duration = performance.now() - t0;
      this.lastError = e?.message ?? "Unknown error";
      
      // Add error message
      const errorMsg: ChatMsg = {
        id: `${Date.now()}_error`,
        role: "assistant", 
        text: `Sorry, I encountered an error: ${this.lastError}`,
        createdAt: Date.now(),
        error: true
      };
      
      this.messages.push(errorMsg);
      
      // Telemetry: request failed
      console.log(`[telemetry] chat_error ${requestId} timing_ms=${Math.round(duration)} error=${e?.message}`);
      
    } finally {
      this.loading = false;
    }
  }

  async clear() {
    this.messages = [];
    this.lastError = null;
    this.sessionId = await clearSession();
    await this.saveMessages();
    console.log('🗑️ Chat cleared, new session:', this.sessionId.substring(0, 8) + '...');
  }

  private async loadMessages() {
    try {
      const key = `stryda.chat.msgs.${this.sessionId}`;
      const stored = await AsyncStorage.getItem(key);
      
      if (stored) {
        this.messages = JSON.parse(stored);
        console.log('📱 Loaded messages:', this.messages.length);
      }
    } catch (error) {
      console.error('❌ Failed to load messages:', error);
      this.messages = [];
    }
  }

  private async saveMessages() {
    try {
      const key = `stryda.chat.msgs.${this.sessionId}`;
      // Keep last 50 messages for performance
      const messagesToSave = this.messages.slice(-50);
      await AsyncStorage.setItem(key, JSON.stringify(messagesToSave));
      console.log('💾 Messages saved:', messagesToSave.length);
    } catch (error) {
      console.error('❌ Failed to save messages:', error);
    }
  }

  logMetric(name: string, ms: number) {
    console.log(`[telemetry] ${name} ${Math.round(ms)}ms`);
  }
}

export const chatStore = new ChatStore();