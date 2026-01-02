import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { ChatMessage, Citation } from '../types/chat';
import CitationPill from './CitationPill';
import ComplianceModal from './ComplianceModal';

interface ChatMessageProps {
  message: ChatMessage;
  onCitationPress: (citation: Citation) => void;
  onRetry?: (messageId: string) => void;
}

export function ChatMessageComponent({ message, onCitationPress, onRetry }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<{source: string, clause: string, page: string} | null>(null);

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

  // Regex to parse the hybrid citation format
  const citationRegex = /\[\[Source:\s*(.*?)\s*\|\s*Clause:\s*(.*?)\s*\|\s*Page:\s*(.*?)\]\]/g;
  const matches = [...(message.text || '').matchAll(citationRegex)];
  const cleanText = (message.text || '').replace(citationRegex, '').trim();

  return (
    <View style={[styles.messageContainer, isUser ? styles.userContainer : styles.assistantContainer]}>
      {/* Message bubble */}
      <View style={[
        styles.messageBubble,
        isUser ? styles.userBubble : styles.assistantBubble,
        message.error && styles.errorBubble
      ]}>
        {/* Loading indicator */}
        {message.loading && isAssistant && (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>STRYDA is thinking...</Text>
          </View>
        )}
        
        {/* Message text */}
        {!message.loading && (
          <View>
              <Text style={[
                styles.messageText,
                isUser ? styles.userText : styles.assistantText
              ]}>
                {cleanText}
              </Text>

              {/* Parsed Citation Pills */}
              {matches.map((match, i) => (
                <TouchableOpacity 
                    key={`parsed-${i}`} 
                    onPress={() => {
                        setSelectedMatch({
                            source: match[1].trim(),
                            clause: match[2].trim(),
                            page: match[3].trim()
                        });
                        setModalVisible(true);
                    }} 
                    style={styles.pillButton}
                >
                    <Text style={styles.pillText}>
                        View Source: {match[1].trim()} {match[2].trim()}
                    </Text>
                </TouchableOpacity>
              ))}
          </View>
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
      
      {/* Timestamp */}
      <View style={[styles.timestampContainer, isUser ? styles.userTimestamp : styles.assistantTimestamp]}>
        <Text style={styles.timestampText}>
          {formatTime(message.ts)}
        </Text>
      </View>

      {/* Compliance Modal */}
      {selectedMatch && (
          <ComplianceModal 
            visible={modalVisible}
            onClose={() => setModalVisible(false)}
            source={selectedMatch.source}
            clause={selectedMatch.clause}
            page={selectedMatch.page}
          />
      )}
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
    maxWidth: '85%',
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
  pillButton: {
      marginTop: 12,
      backgroundColor: '#F97316',
      paddingVertical: 10,
      paddingHorizontal: 16,
      borderRadius: 12,
      alignSelf: 'flex-start',
  },
  pillText: {
      color: 'white',
      fontWeight: 'bold',
      fontSize: 14,
  }
});

export default ChatMessageComponent;
