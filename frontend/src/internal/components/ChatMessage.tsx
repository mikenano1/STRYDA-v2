/**
 * Chat Message Component
 * Renders user/assistant messages with citations and error states
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { ChatMessage, Citation } from '../types/chat';
import CitationPill from './CitationPill';

interface ChatMessageProps {
  message: ChatMessage;
  onCitationPress: (citation: Citation) => void;
  onRetry?: (messageId: string) => void;
}

export function ChatMessageComponent({ message, onCitationPress, onRetry }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  // Format timestamp
  const formatTime = (ts: number) => {
    const date = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleRetry = () => {
    if (onRetry) {
      console.log('🔄 Retry requested for message:', message.id);
      onRetry(message.id);
    }
  };

  return (
    <View style={[styles.messageContainer, isUser ? styles.userContainer : styles.assistantContainer]}>
      {/* Message bubble */}
      <View style={[
        styles.messageBubble,
        isUser ? styles.userBubble : styles.assistantBubble,
        message.error && styles.errorBubble
      ]}>
        {/* Loading indicator for assistant */}
        {message.loading && isAssistant && (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>STRYDA is thinking...</Text>
          </View>
        )}
        
        {/* Message text */}
        {!message.loading && (
          <Text style={[
            styles.messageText,
            isUser ? styles.userText : styles.assistantText
          ]}>
            {message.text}
          </Text>
        )}
        
        {/* Error state with retry */}
        {message.error && (
          <TouchableOpacity 
            style={styles.retryButton}
            onPress={handleRetry}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        )}
      </View>
      
      {/* Citations (assistant only) */}
      {isAssistant && message.citations && message.citations.length > 0 && !message.loading && (
        <View style={styles.citationsContainer}>
          {message.citations.map((citation, index) => (
            <CitationPill
              key={`${citation.source}-${citation.page}-${index}`}
              citation={citation}
              onPress={onCitationPress}
            />
          ))}
        </View>
      )}
      
      {/* Timestamp */}
      <View style={[styles.timestampContainer, isUser ? styles.userTimestamp : styles.assistantTimestamp]}>
        <Text style={styles.timestampText}>
          {formatTime(message.ts)}
        </Text>
        
        {/* Debug timing (development only) */}
        {__DEV__ && isAssistant && message.timing_ms && (
          <Text style={styles.debugTiming}>
            ({(message.timing_ms / 1000).toFixed(1)}s)
          </Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  messageContainer: {
    marginVertical: 8,
    marginHorizontal: 16,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#FF7A00', // Orange accent
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#2A2A2A', // Dark gray
    borderBottomLeftRadius: 4,
  },
  errorBubble: {
    backgroundColor: '#FF4444', // Error red
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#000000', // Black on orange
    fontWeight: '500',
  },
  assistantText: {
    color: '#FFFFFF', // White on dark
  },
  loadingContainer: {
    paddingVertical: 4,
  },
  loadingText: {
    color: '#CCCCCC',
    fontSize: 14,
    fontStyle: 'italic',
  },
  retryButton: {
    marginTop: 8,
    backgroundColor: '#FFFFFF20',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  retryText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  citationsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
    maxWidth: '80%',
  },
  timestampContainer: {
    marginTop: 4,
  },
  userTimestamp: {
    alignItems: 'flex-end',
  },
  assistantTimestamp: {
    alignItems: 'flex-start',
  },
  timestampText: {
    color: '#888888',
    fontSize: 12,
  },
  debugTiming: {
    color: '#666666',
    fontSize: 10,
    marginTop: 2,
  }
});

export default ChatMessageComponent;