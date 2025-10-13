/**
 * Minimal Telemetry System for STRYDA Chat
 * Events: chat_request_started, chat_request_succeeded, chat_request_failed, citation_pill_opened
 * No secrets, no message content, session-aware
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

interface TelemetryEvent {
  event: string;
  session_id: string;
  timestamp: number;
  properties?: Record<string, any>;
}

interface ChatRequestStartedEvent {
  event: 'chat_request_started';
  session_id: string;
  message_length: number;
  turn_number: number;
}

interface ChatRequestSucceededEvent {
  event: 'chat_request_succeeded';
  session_id: string;
  timing_ms: number;
  citations_count: number;
  response_length: number;
}

interface ChatRequestFailedEvent {
  event: 'chat_request_failed';
  session_id: string;
  timing_ms: number;
  error_type: string;
}

interface CitationPillOpenedEvent {
  event: 'citation_pill_opened';
  session_id: string;
  source: string;
  page: number;
  score: number;
  has_section: boolean;
  has_clause: boolean;
}

export class Telemetry {
  private static events: TelemetryEvent[] = [];
  
  /**
   * Log telemetry event with privacy protection
   */
  static logEvent(event: TelemetryEvent) {
    // Add timestamp
    const eventWithTimestamp = {
      ...event,
      timestamp: Date.now(),
    };
    
    // Store locally
    this.events.push(eventWithTimestamp);
    
    // Console logging for development
    if (__DEV__) {
      console.log('📊 Telemetry:', {
        event: event.event,
        session_id: event.session_id.substring(0, 8) + '...',
        properties: event.properties
      });
    }
    
    // Optional: send to backend metrics endpoint (if available)
    this.sendToBackend(eventWithTimestamp);
  }
  
  /**
   * Chat request started event
   */
  static chatRequestStarted(sessionId: string, messageLength: number, turnNumber: number) {
    this.logEvent({
      event: 'chat_request_started',
      session_id: sessionId,
      timestamp: Date.now(),
      properties: {
        message_length: messageLength,
        turn_number: turnNumber
      }
    });
  }
  
  /**
   * Chat request succeeded event
   */
  static chatRequestSucceeded(sessionId: string, timingMs: number, citationsCount: number, responseLength: number) {
    this.logEvent({
      event: 'chat_request_succeeded',
      session_id: sessionId,
      timestamp: Date.now(),
      properties: {
        timing_ms: timingMs,
        citations_count: citationsCount,
        response_length: responseLength
      }
    });
  }
  
  /**
   * Chat request failed event
   */
  static chatRequestFailed(sessionId: string, timingMs: number, errorType: string) {
    this.logEvent({
      event: 'chat_request_failed',
      session_id: sessionId,
      timestamp: Date.now(),
      properties: {
        timing_ms: timingMs,
        error_type: errorType
      }
    });
  }
  
  /**
   * Citation pill opened event
   */
  static citationPillOpened(sessionId: string, source: string, page: number, score: number, hasSection: boolean, hasClause: boolean) {
    this.logEvent({
      event: 'citation_pill_opened',
      session_id: sessionId,
      timestamp: Date.now(),
      properties: {
        source,
        page,
        score,
        has_section: hasSection,
        has_clause: hasClause
      }
    });
  }
  
  /**
   * Send event to backend metrics endpoint (optional)
   */
  private static async sendToBackend(event: TelemetryEvent) {
    try {
      const API_BASE = process.env.EXPO_PUBLIC_API_BASE;
      if (!API_BASE) return;
      
      // Try to send to metrics endpoint (fire and forget)
      fetch(`${API_BASE}/api/metrics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
        timeout: 5000
      }).catch(() => {
        // Silently fail - metrics are not critical
      });
      
    } catch (error) {
      // Silent failure - telemetry should never break the app
    }
  }
  
  /**
   * Get recent events for debugging
   */
  static getRecentEvents(limit = 10): TelemetryEvent[] {
    return this.events.slice(-limit);
  }
  
  /**
   * Clear old events (privacy)
   */
  static clearOldEvents() {
    // Keep only last 100 events
    if (this.events.length > 100) {
      this.events = this.events.slice(-100);
    }
  }
}

export default Telemetry;