import { useState, useEffect } from 'react';
import { Text, View, StyleSheet, TextInput, TouchableOpacity, Alert, ScrollView, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { API_BASE } from '../internal/config/constants';
import { chatAPI } from '../internal/lib/api';
import { DEV_DIAG } from '../internal/diag';
import DiagOverlay from '../internal/DiagOverlay';

const theme = { 
  bg: '#111111', 
  text: '#FFFFFF', 
  muted: '#A7A7A7', 
  accent: '#FF7A00', 
  inputBg: '#1A1A1A' 
};

// Add explicit types and safe parsing
type Msg = { id: string; role: 'user'|'assistant'; text: string; citations?: any[]; timestamp: number };

interface Citation {
  source: string;
  page: number;
  score?: number;
  snippet?: string;
  section?: string;
  clause?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
  timestamp: number;
}

export default function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState('');
  const [expandedCitation, setExpandedCitation] = useState<Citation | null>(null);

  // Initialize session and diagnostic logs
  useEffect(() => {
    const initializeApp = async () => {
      // 1) Log API_BASE
      const apiBase = process.env.EXPO_PUBLIC_API_BASE || 'http://localhost:8001';
      console.log('🔧 EXPO_PUBLIC_API_BASE:', apiBase);
      
      // 2) Health check
      try {
        const healthResponse = await fetch(`${apiBase}/health`);
        const healthData = await healthResponse.json();
        console.log('✅ Health check result:', healthData);
      } catch (error) {
        console.error('❌ Health check failed:', error);
      }
      
      // 3) Generate session ID
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      console.log('🔄 Chat session initialized:', newSessionId.substring(0, 15) + '...');
    };
    
    initializeApp();
  }, []);

  const sendMessage = async () => {
    // Safe parsing with defensive coding
    const userText = inputText.trim();
    if (!userText || isSending) {
      console.log('⚠️ Send blocked:', { userText: userText.length, isSending });
      return;
    }
    
    if (!sessionId) {
      console.log('❌ No session ID available');
      return;
    }
    
    // Create user message
    const userMsg: Msg = { 
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`, 
      role: 'user', 
      text: userText,
      timestamp: Date.now()
    };
    
    // Clear input and add user message (functional update)
    setInputText('');
    setMessages(prev => [...prev, userMsg]);
    setIsSending(true);
    
    // Telemetry: chat_send
    console.log(`[telemetry] chat_send session_id=${sessionId.substring(0, 8)}... input_length=${userText.length}`);
    
    try {
      console.log('🎯 POST /api/chat:', { 
        session_id: sessionId.substring(0, 10) + '...',
        message_len: userText.length 
      });
      
      // Use centralized API client
      const res = await chatAPI({
        session_id: sessionId,
        message: userText
      });
      
      // DEBUG: Log complete server response
      console.log('SERVER_RESPONSE', JSON.stringify(res, null, 2));
      
      // Normalize response with fallback chain
      const answer = (res && (res.answer || res.message || res?.output?.text || res?.data?.answer)) ?? '';
      const assistantText = String(answer).trim();
      
      console.log('🎯 Response parsed:', { 
        messageLength: assistantText.length,
        citationsCount: res.citations?.length || 0,
        intent: res.intent,
        timingMs: res.timing_ms
      });
      
      // Guard against accidental echo
      if (assistantText === userText && assistantText !== '') {
        console.warn('⚠️ Echo detected; response matches user input');
      }
      
      // Create assistant message with safe parsing
      const assistantMsg: Msg = {
        id: `assistant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        text: assistantText || '(no answer received)',
        citations: res?.citations || res?.data?.citations || [],
        timestamp: Date.now()
      };
      
      // Telemetry: chat_response
      console.log(`[telemetry] chat_response timing_ms=${res.timing_ms || 0} citations_count=${res.citations?.length || 0}`);
      
      setMessages(prev => [...prev, assistantMsg]);
      
      // Optimistic health update on successful chat
      setHealthStatus('ok');
      setHealthFailureCount(0);
      
    } catch (error: any) {
      console.error('❌ Chat request failed:', error);
      
      // Telemetry: chat_error  
      console.log(`[telemetry] chat_error error=${error.message.substring(0, 50)}`);
      
      // Add error message with retry
      const errorMsg: Msg = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        text: `Couldn't reach server. ${error.message}`,
        timestamp: Date.now()
      };
      
      setMessages(prev => [...prev, errorMsg]);
      
      // Update health status
      setHealthStatus('failed');
      
      Alert.alert(
        'Connection Error',
        `Failed to get response from STRYDA: ${error.message}`,
        [
          { text: 'OK' },
          { text: 'Retry', onPress: () => sendMessage() }
        ]
      );
      
    } finally {
      setIsSending(false);
    }
  };

  const handleCitationPress = (citation: Citation) => {
    console.log('[telemetry] citation_pill_opened', {
      source: citation.source,
      page: citation.page,
      score: citation.score
    });
    
    setExpandedCitation(expandedCitation?.page === citation.page ? null : citation);
  };

  const handleNewChat = () => {
    Alert.alert(
      'New Chat',
      'Start a new conversation? Current chat will be cleared.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'New Chat', 
          onPress: () => {
            setMessages([]);
            const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            setSessionId(newSessionId);
            console.log('🆕 New chat session started:', newSessionId.substring(0, 15) + '...');
          }
        }
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>STRYDA.ai</Text>
          <Text style={styles.apiDebug}>API: {(process.env.EXPO_PUBLIC_API_BASE || 'preview').split('//')[1]}</Text>
          <Text style={styles.routeDebug}>Route: /api/chat</Text>
        </View>
        <TouchableOpacity 
          style={styles.newChatButton}
          onPress={handleNewChat}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Text style={styles.newChatText}>New Chat</Text>
        </TouchableOpacity>
      </View>
      
      {/* Messages Area */}
      <View style={styles.messagesContainer}>
        {messages.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>Ask STRYDA about:</Text>
            <Text style={styles.emptyHint}>• Flashing cover requirements</Text>
            <Text style={styles.emptyHint}>• High wind zone standards</Text>
            <Text style={styles.emptyHint}>• Metal roofing fixings</Text>
            <Text style={styles.emptyHint}>• Building code compliance</Text>
          </View>
        ) : (
          <ScrollView 
            style={styles.messagesList}
            contentContainerStyle={styles.messagesContent}
            showsVerticalScrollIndicator={false}
          >
            {messages.map((message) => (
              <View 
                key={message.id} 
                style={[
                  styles.messageContainer,
                  message.role === 'user' ? styles.userMessage : styles.assistantMessage
                ]}
              >
                <View style={[
                  styles.messageBubble,
                  message.role === 'user' ? styles.userBubble : styles.assistantBubble
                ]}>
                  <Text style={[
                    styles.messageText,
                    message.role === 'user' ? styles.userText : styles.assistantText
                  ]}>
                    {message.text}
                  </Text>
                </View>
                
                {/* Citations */}
                {message.role === 'assistant' && message.citations && message.citations.length > 0 && (
                  <View style={styles.citationsContainer}>
                    {message.citations.map((citation, index) => (
                      <TouchableOpacity
                        key={`${citation.source}-${citation.page}-${index}`}
                        style={styles.citationPill}
                        onPress={() => handleCitationPress(citation)}
                        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                      >
                        <Text style={styles.citationText}>
                          {citation.source} p.{citation.page}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
                
                {/* Expanded Citation */}
                {expandedCitation && expandedCitation.source && 
                 message.citations?.some(c => c.page === expandedCitation.page) && (
                  <View style={styles.expandedCitation}>
                    <Text style={styles.expandedCitationTitle}>
                      {expandedCitation.source} • Page {expandedCitation.page}
                    </Text>
                    
                    {expandedCitation.snippet && (
                      <Text style={styles.expandedCitationSnippet}>
                        {expandedCitation.snippet}
                      </Text>
                    )}
                    
                    <View style={styles.citationMeta}>
                      {expandedCitation.score && (
                        <Text style={styles.metaText}>
                          Relevance: {(expandedCitation.score * 100).toFixed(0)}%
                        </Text>
                      )}
                      {expandedCitation.section && (
                        <Text style={styles.metaText}>
                          Section: {expandedCitation.section.substring(0, 30)}...
                        </Text>
                      )}
                      {expandedCitation.clause && (
                        <Text style={styles.metaText}>
                          Clause: {expandedCitation.clause}
                        </Text>
                      )}
                    </View>
                  </View>
                )}
              </View>
            ))}
          </ScrollView>
        )}
        
        {/* Loading indicator */}
        {isSending && (
          <View style={styles.loadingContainer}>
            <View style={styles.loadingBubble}>
              <ActivityIndicator size="small" color={theme.muted} />
              <Text style={styles.loadingText}>STRYDA is thinking...</Text>
            </View>
          </View>
        )}
      </View>
      
      {/* Input Area */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          placeholder="Ask STRYDA…"
          placeholderTextColor={theme.muted}
          value={inputText}
          onChangeText={setInputText}
          multiline
          maxLength={1000}
          editable={!isSending}
          returnKeyType="send"
          onSubmitEditing={sendMessage}
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            (!inputText.trim() || isSending) && styles.sendButtonDisabled
          ]}
          onPress={() => {
            console.log('🎯 CHAT TAB - Send button onPress triggered');
            sendMessage();
          }}
          disabled={!inputText.trim() || isSending}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          {isSending ? (
            <ActivityIndicator size="small" color="#000000" />
          ) : (
            <Text style={styles.sendButtonText}>Send</Text>
          )}
        </TouchableOpacity>
      </View>
      
      {/* Diagnostic Overlay (dev only) */}
      {DEV_DIAG ? <DiagOverlay /> : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.bg,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  headerTitle: {
    color: theme.text,
    fontSize: 24,
    fontWeight: 'bold',
  },
  apiDebug: {
    color: '#888888',
    fontSize: 10,
    marginTop: 2,
  },
  routeDebug: {
    color: '#666666',
    fontSize: 9,
    marginTop: 1,
  },
  newChatButton: {
    backgroundColor: theme.accent,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  newChatText: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
  },
  messagesContainer: {
    flex: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyTitle: {
    color: theme.text,
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 20,
    textAlign: 'center',
  },
  emptyHint: {
    color: theme.muted,
    fontSize: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  messagesList: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
  },
  messageContainer: {
    marginBottom: 16,
  },
  userMessage: {
    alignItems: 'flex-end',
  },
  assistantMessage: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 16,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: theme.accent,
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#2A2A2A',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#000000',
    fontWeight: '500',
  },
  assistantText: {
    color: theme.text,
  },
  citationsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 12,
    maxWidth: '80%',
  },
  citationPill: {
    backgroundColor: theme.accent,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 6,
    minHeight: 44,
  },
  citationText: {
    color: '#000000',
    fontSize: 12,
    fontWeight: '600',
  },
  expandedCitation: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    maxWidth: '80%',
  },
  expandedCitationTitle: {
    color: theme.accent,
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  expandedCitationSnippet: {
    color: theme.muted,
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  citationMeta: {
    backgroundColor: '#0A0A0A',
    borderRadius: 8,
    padding: 12,
  },
  metaText: {
    color: '#888888',
    fontSize: 12,
    marginBottom: 4,
  },
  loadingContainer: {
    alignItems: 'flex-start',
    padding: 16,
  },
  loadingBubble: {
    backgroundColor: '#2A2A2A',
    borderRadius: 16,
    borderBottomLeftRadius: 4,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    maxWidth: '80%',
  },
  loadingText: {
    color: theme.muted,
    fontSize: 14,
    marginLeft: 8,
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 20,
    backgroundColor: '#0A0A0A',
    borderTopWidth: 1,
    borderTopColor: '#333333',
  },
  textInput: {
    flex: 1,
    backgroundColor: theme.inputBg,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: theme.text,
    marginRight: 12,
    maxHeight: 100,
    minHeight: 44,
  },
  sendButton: {
    backgroundColor: theme.accent,
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 44,
    minWidth: 60,
  },
  sendButtonDisabled: {
    backgroundColor: '#555555',
  },
  sendButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: 'bold',
  },
});