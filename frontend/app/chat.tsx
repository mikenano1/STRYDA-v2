import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  citations?: Citation[];
  confidence_score?: number;
  sources_used?: string[];
  compliance_issues?: ComplianceIssue[];
  processing_time_ms?: number;
}

interface Citation {
  chunk_id: string;
  title: string;
  url?: string;
  snippet?: string;
  document_type?: string;
}

interface ComplianceIssue {
  description: string;
  severity: string;
  code_reference: string;
  alternatives?: any[];
}

export default function ChatScreen() {
  const params = useLocalSearchParams();
  const initialMessage = params.message as string;
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    // If there's an initial message from the home screen, send it
    if (initialMessage && messages.length === 0) {
      sendMessage(initialMessage);
    }
  }, [initialMessage]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages are added
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages]);

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() && !initialMessage) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText || initialMessage,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Call the enhanced backend API for AI response
      const response = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/chat/enhanced`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText || initialMessage,
          session_id: 'mobile_app_session',
          enable_compliance_analysis: true,
          enable_query_processing: true,
        }),
      });

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response || "I'm still learning about NZ building codes. Can you try rephrasing your question?",
        sender: 'bot',
        timestamp: new Date(),
        citations: data.citations || [],
        confidence_score: data.confidence_score,
        sources_used: data.sources_used || [],
        compliance_issues: data.compliance_issues || [],
        processing_time_ms: data.processing_time_ms,
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I'm having trouble connecting right now. Please check your connection and try again.",
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (message: Message) => {
    const isUser = message.sender === 'user';
    
    return (
      <View key={message.id} style={[styles.messageContainer, isUser && styles.userMessageContainer]}>
        <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.botBubble]}>
          <Text style={[styles.messageText, isUser && styles.userMessageText]}>
            {message.text}
          </Text>
          
          {/* Enhanced information for bot messages */}
          {!isUser && (
            <View style={styles.enhancedInfoContainer}>
              {/* Confidence Score */}
              {message.confidence_score && (
                <View style={styles.confidenceContainer}>
                  <IconSymbol name="chart.bar.fill" size={12} color={Colors.dark.tint} />
                  <Text style={styles.confidenceText}>
                    {Math.round(message.confidence_score * 100)}% confidence
                  </Text>
                </View>
              )}
              
              {/* Processing Time */}
              {message.processing_time_ms && (
                <View style={styles.processingTimeContainer}>
                  <IconSymbol name="clock" size={12} color={Colors.dark.icon} />
                  <Text style={styles.processingTimeText}>
                    {(message.processing_time_ms / 1000).toFixed(1)}s
                  </Text>
                </View>
              )}
            </View>
          )}
          
          {/* Compliance Issues */}
          {message.compliance_issues && message.compliance_issues.length > 0 && (
            <View style={styles.complianceContainer}>
              <View style={styles.complianceHeader}>
                <IconSymbol name="exclamationmark.triangle.fill" size={14} color="#FF6B6B" />
                <Text style={styles.complianceTitle}>Compliance Alert</Text>
              </View>
              {message.compliance_issues.map((issue, index) => (
                <View key={index} style={styles.complianceIssue}>
                  <Text style={styles.issueDescription}>{issue.description}</Text>
                  <Text style={styles.issueReference}>
                    {issue.code_reference} • {issue.severity}
                  </Text>
                </View>
              ))}
            </View>
          )}
          
          {/* Sources Used */}
          {message.sources_used && message.sources_used.length > 0 && (
            <View style={styles.sourcesContainer}>
              <Text style={styles.sourcesTitle}>Sources:</Text>
              <View style={styles.sourcesGrid}>
                {message.sources_used.slice(0, 3).map((source, index) => (
                  <View key={index} style={styles.sourceChip}>
                    <Text style={styles.sourceText} numberOfLines={1}>
                      {source.replace(/^(NZBC|MANUFACTURER|NZS):\s*/, '')}
                    </Text>
                  </View>
                ))}
                {message.sources_used.length > 3 && (
                  <Text style={styles.moreSourcesText}>
                    +{message.sources_used.length - 3} more
                  </Text>
                )}
              </View>
            </View>
          )}
          
          {/* Citations */}
          {message.citations && message.citations.length > 0 && (
            <View style={styles.citationsContainer}>
              <Text style={styles.citationsTitle}>References:</Text>
              {message.citations.slice(0, 2).map((citation) => (
                <TouchableOpacity key={citation.chunk_id} style={styles.citation}>
                  <IconSymbol 
                    name={citation.document_type === 'nzbc' ? 'doc.text.fill' : 'building.2.fill'} 
                    size={14} 
                    color={Colors.dark.tint} 
                  />
                  <View style={styles.citationContent}>
                    <Text style={styles.citationTitle} numberOfLines={2}>
                      {citation.title}
                    </Text>
                    {citation.snippet && (
                      <Text style={styles.citationSnippet} numberOfLines={2}>
                        {citation.snippet}
                      </Text>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
              {message.citations.length > 2 && (
                <Text style={styles.moreCitationsText}>
                  View {message.citations.length - 2} more references in Library
                </Text>
              )}
            </View>
          )}
        </View>
        
        <Text style={styles.timestamp}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardContainer}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={() => router.back()}
          >
            <IconSymbol name="chevron.left" size={20} color={Colors.dark.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>STRYDA Chat</Text>
          <TouchableOpacity style={styles.headerAction}>
            <IconSymbol name="ellipsis" size={20} color={Colors.dark.icon} />
          </TouchableOpacity>
        </View>

        {/* Messages */}
        <ScrollView 
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
        >
          {messages.length === 0 && !isLoading && (
            <View style={styles.welcomeContainer}>
              <Text style={styles.welcomeText}>
                Ask me anything about NZ building codes, compliance, or product specifications. 
                I'll provide answers with proper citations from official sources.
              </Text>
            </View>
          )}
          
          {messages.map(renderMessage)}
          
          {/* Loading indicator */}
          {isLoading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color={Colors.dark.tint} />
              <Text style={styles.loadingText}>STRYDA is thinking...</Text>
            </View>
          )}
        </ScrollView>

        {/* Input */}
        <View style={styles.inputContainer}>
          <View style={styles.inputWrapper}>
            <TextInput
              style={styles.textInput}
              placeholder="Ask about codes, clearances, compliance..."
              placeholderTextColor={Colors.dark.placeholder}
              value={inputText}
              onChangeText={setInputText}
              multiline
              maxLength={500}
              returnKeyType="send"
              onSubmitEditing={() => sendMessage(inputText)}
              blurOnSubmit={false}
            />
            
            <TouchableOpacity 
              style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
              onPress={() => sendMessage(inputText)}
              disabled={!inputText.trim() || isLoading}
              activeOpacity={0.8}
            >
              <IconSymbol 
                name="paperplane.fill" 
                size={18} 
                color={inputText.trim() && !isLoading ? Colors.dark.background : Colors.dark.placeholder} 
              />
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.dark.background,
  },
  keyboardContainer: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.dark.border,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.dark.text,
  },
  headerAction: {
    padding: 8,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 20,
    paddingBottom: 10,
  },
  welcomeContainer: {
    alignItems: 'center',
    paddingVertical: 40,
    paddingHorizontal: 20,
  },
  welcomeText: {
    fontSize: 16,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 22,
  },
  messageContainer: {
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  userMessageContainer: {
    alignItems: 'flex-end',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 4,
  },
  userBubble: {
    backgroundColor: Colors.dark.messageUser,
    borderBottomRightRadius: 4,
  },
  botBubble: {
    backgroundColor: Colors.dark.messageBot,
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    color: Colors.dark.messageText,
    lineHeight: 20,
  },
  userMessageText: {
    color: Colors.dark.background,
  },
  timestamp: {
    fontSize: 12,
    color: Colors.dark.placeholder,
    marginHorizontal: 4,
  },
  citationsContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.dark.border + '40',
  },
  citationsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.dark.icon,
    marginBottom: 8,
  },
  citation: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 6,
    gap: 8,
  },
  citationContent: {
    flex: 1,
  },
  citationTitle: {
    fontSize: 12,
    color: Colors.dark.text,
    fontWeight: '500',
    marginBottom: 2,
  },
  citationSnippet: {
    fontSize: 11,
    color: Colors.dark.icon,
    lineHeight: 14,
  },
  moreCitationsText: {
    fontSize: 11,
    color: Colors.dark.tint,
    fontStyle: 'italic',
    marginTop: 4,
  },
  enhancedInfoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 8,
  },
  confidenceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  confidenceText: {
    fontSize: 11,
    color: Colors.dark.tint,
    fontWeight: '500',
  },
  processingTimeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  processingTimeText: {
    fontSize: 11,
    color: Colors.dark.icon,
  },
  complianceContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#FF6B6B40',
    backgroundColor: '#FF6B6B10',
    borderRadius: 8,
    padding: 8,
  },
  complianceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  complianceTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FF6B6B',
  },
  complianceIssue: {
    marginBottom: 4,
  },
  issueDescription: {
    fontSize: 12,
    color: Colors.dark.text,
    marginBottom: 2,
  },
  issueReference: {
    fontSize: 11,
    color: Colors.dark.icon,
    fontStyle: 'italic',
  },
  sourcesContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.dark.border + '40',
  },
  sourcesTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.dark.icon,
    marginBottom: 6,
  },
  sourcesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    alignItems: 'center',
  },
  sourceChip: {
    backgroundColor: Colors.dark.tint + '20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    maxWidth: 120,
  },
  sourceText: {
    fontSize: 11,
    color: Colors.dark.tint,
    fontWeight: '500',
  },
  moreSourcesText: {
    fontSize: 11,
    color: Colors.dark.icon,
    fontStyle: 'italic',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 12,
  },
  loadingText: {
    fontSize: 14,
    color: Colors.dark.icon,
  },
  inputContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.dark.border,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: Colors.dark.inputBackground,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: Colors.dark.text,
    maxHeight: 100,
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.dark.tint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: Colors.dark.surface,
  },
});