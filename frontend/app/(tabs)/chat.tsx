/**
 * Main Chat Screen with Multi-Turn Conversations
 * Features: Session memory, citations, loading states, error handling
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import BottomSheet, { BottomSheetModalProvider, BottomSheetModal } from '@gorhom/bottom-sheet';
import { useChatMessages, useSessionId, useIsInitialized, useChatActions } from '../state/chatStore';
import { postChat, APIError } from '../lib/api';
import ChatMessageComponent from '../components/ChatMessage';
import { ChatMessage, Citation } from '../types/chat';

export default function ChatScreen() {
  // Store state
  const messages = useChatMessages();
  const sessionId = useSessionId();
  const isInitialized = useIsInitialized();
  const { addMessage, updateMessage, markFailed, initialize, createNewSession } = useChatActions();
  
  // Local state
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  
  // Refs
  const flatListRef = useRef<FlatList>(null);
  const bottomSheetRef = useRef<BottomSheetModal>(null);
  const snapPoints = ['25%', '60%'];
  
  // Initialize store on mount
  useEffect(() => {
    if (!isInitialized) {
      initialize();
    }
  }, [isInitialized, initialize]);
  
  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length]);
  
  const sendMessage = useCallback(async () => {
    if (!inputText.trim() || isSending || !sessionId) return;
    
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const userMessage: ChatMessage = {
      id: messageId,
      role: 'user',
      text: inputText.trim(),
      ts: Date.now(),
    };
    
    // Clear input and add user message
    const messageToSend = inputText.trim();
    setInputText('');
    addMessage(userMessage);
    
    // Add loading assistant message
    const assistantMessageId = `msg_${Date.now()}_assistant`;
    const loadingMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      text: '',
      ts: Date.now(),
      loading: true,
    };
    
    addMessage(loadingMessage);
    setIsSending(true);
    
    try {
      // Call chat API
      const response = await postChat({
        session_id: sessionId,
        message: messageToSend,
      });
      
      // Update assistant message with response
      updateMessage(assistantMessageId, {
        text: response.message,
        citations: response.citations || [],
        loading: false,
        timing_ms: response.timing_ms,
      });
      
    } catch (error) {
      console.error('❌ Chat request failed:', error);
      
      // Mark assistant message as failed
      updateMessage(assistantMessageId, {
        text: error instanceof APIError 
          ? `Sorry, I encountered an error: ${error.message}` 
          : 'Sorry, I had trouble connecting. Please try again.',
        loading: false,
        error: true,
      });
      
      // Show toast error
      if (error instanceof APIError && error.status === 0) {
        Alert.alert('Connection Error', "Couldn't reach STRYDA. Check your connection and try again.");
      }
      
    } finally {
      setIsSending(false);
    }
  }, [inputText, isSending, sessionId, addMessage, updateMessage]);
  
  const handleCitationPress = useCallback((citation: Citation) => {
    console.log('📄 Opening citation details:', citation);
    setSelectedCitation(citation);
    bottomSheetRef.current?.present();
  }, []);
  
  const handleRetry = useCallback(async (messageId: string) => {
    // Find the message to retry
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    if (messageIndex === -1) return;
    
    const message = messages[messageIndex];
    if (message.role !== 'assistant') return;
    
    // Find the user message that prompted this
    const userMessage = messages[messageIndex - 1];
    if (!userMessage || userMessage.role !== 'user') return;
    
    // Reset the assistant message to loading
    updateMessage(messageId, {
      loading: true,
      error: false,
      text: '',
    });
    
    setIsSending(true);
    
    try {
      const response = await postChat({
        session_id: sessionId,
        message: userMessage.text,
      });
      
      updateMessage(messageId, {
        text: response.message,
        citations: response.citations || [],
        loading: false,
        error: false,
      });
      
    } catch (error) {
      console.error('❌ Retry failed:', error);
      updateMessage(messageId, {
        text: 'Retry failed. Please try asking again.',
        loading: false,
        error: true,
      });
      
    } finally {
      setIsSending(false);
    }
  }, [messages, sessionId, updateMessage]);
  
  const handleNewChat = useCallback(async () => {
    Alert.alert(
      'New Chat', 
      'Start a new conversation? Current chat will be saved.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'New Chat', 
          style: 'default',
          onPress: async () => {
            await createNewSession();
            console.log('🆕 Started new chat session');
          }
        }
      ]
    );
  }, [createNewSession]);
  
  const renderMessage = useCallback(({ item }: { item: ChatMessage }) => (
    <ChatMessageComponent
      message={item}
      onCitationPress={handleCitationPress}
      onRetry={handleRetry}
    />
  ), [handleCitationPress, handleRetry]);
  
  const keyExtractor = useCallback((item: ChatMessage) => item.id, []);
  
  if (!isInitialized) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF7A00" />
        <Text style={styles.loadingText}>Loading chat...</Text>
      </SafeAreaView>
    );
  }
  
  return (
    <BottomSheetModalProvider>
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>STRYDA.ai</Text>
          <TouchableOpacity 
            style={styles.newChatButton}
            onPress={handleNewChat}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={styles.newChatText}>New Chat</Text>
          </TouchableOpacity>
        </View>
        
        {/* Chat area */}
        <KeyboardAvoidingView 
          style={styles.chatContainer}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          {/* Messages */}
          {messages.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyTitle}>Ask STRYDA about:</Text>
              <Text style={styles.emptyHint}>• Flashing cover requirements</Text>
              <Text style={styles.emptyHint}>• High wind zone standards</Text>
              <Text style={styles.emptyHint}>• Metal roofing fixings</Text>
              <Text style={styles.emptyHint}>• Building code compliance</Text>
            </View>
          ) : (
            <FlatList
              ref={flatListRef}
              data={messages}
              renderItem={renderMessage}
              keyExtractor={keyExtractor}
              style={styles.messagesList}
              contentContainerStyle={styles.messagesContent}
              showsVerticalScrollIndicator={false}
              removeClippedSubviews={false} // Better for citations
            />
          )}
          
          {/* Input bar */}
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.textInput}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Ask STRYDA..."
              placeholderTextColor="#888888"
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
              onPress={sendMessage}
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
        </KeyboardAvoidingView>
        
        {/* Citation Bottom Sheet */}
        <BottomSheetModal
          ref={bottomSheetRef}
          snapPoints={snapPoints}
          enablePanDownToClose
          backgroundStyle={styles.bottomSheetBackground}
          handleIndicatorStyle={styles.bottomSheetIndicator}
        >
          {selectedCitation && (
            <View style={styles.citationDetails}>
              <Text style={styles.citationTitle}>
                {selectedCitation.source} • Page {selectedCitation.page}
              </Text>
              
              {selectedCitation.snippet && (
                <Text style={styles.citationSnippet}>
                  {selectedCitation.snippet}
                </Text>
              )}
              
              <View style={styles.citationMeta}>
                <Text style={styles.citationMetaText}>
                  Relevance: {(selectedCitation.score * 100).toFixed(0)}%
                </Text>
                
                {selectedCitation.section && (
                  <Text style={styles.citationMetaText}>
                    Section: {selectedCitation.section}
                  </Text>
                )}
                
                {selectedCitation.clause && (
                  <Text style={styles.citationMetaText}>
                    Clause: {selectedCitation.clause}
                  </Text>
                )}
              </View>
            </View>
          )}
        </BottomSheetModal>
      </SafeAreaView>
    </BottomSheetModalProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111111', // Dark background
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#111111',
  },
  loadingText: {
    color: '#FFFFFF',
    marginTop: 12,
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: 'bold',
  },
  newChatButton: {
    backgroundColor: '#FF7A00',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  newChatText: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
  },
  chatContainer: {
    flex: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  emptyHint: {
    color: '#CCCCCC',
    fontSize: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  messagesList: {
    flex: 1,
  },
  messagesContent: {
    paddingTop: 16,
    paddingBottom: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 16,
    backgroundColor: '#1A1A1A',
    borderTopWidth: 1,
    borderTopColor: '#333333',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#2A2A2A',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#FFFFFF',
    fontSize: 16,
    maxHeight: 100,
    marginRight: 12,
  },
  sendButton: {
    backgroundColor: '#FF7A00',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 60,
  },
  sendButtonDisabled: {
    backgroundColor: '#555555',
  },
  sendButtonText: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
  },
  // Bottom sheet styles
  bottomSheetBackground: {
    backgroundColor: '#2A2A2A',
  },
  bottomSheetIndicator: {
    backgroundColor: '#666666',
  },
  citationDetails: {
    padding: 20,
  },
  citationTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  citationSnippet: {
    color: '#CCCCCC',
    fontSize: 16,
    lineHeight: 22,
    marginBottom: 16,
  },
  citationMeta: {
    backgroundColor: '#1A1A1A',
    borderRadius: 8,
    padding: 12,
  },
  citationMetaText: {
    color: '#888888',
    fontSize: 14,
    marginBottom: 4,
  },
});

export { ChatScreen };