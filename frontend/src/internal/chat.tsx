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
  Image as RNImage,
  Alert,
  Modal,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { router, useLocalSearchParams } from 'expo-router';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { VoiceController } from '@/components/VoiceController';

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
  image_uri?: string;  // For user uploaded images
  is_vision_response?: boolean;  // For AI vision analysis
  visual_content?: VisualContent[];  // AI-provided diagrams and charts
}

interface Citation {
  id?: string;
  chunk_id?: string;
  title?: string;
  source?: string;
  url?: string;
  snippet?: string;
  text_content?: string;  // Full evidence text for modal display
  document_type?: string;
  page?: number;
  pages?: string;
  clause?: string;
  section?: string;
  pill_text?: string;
}

interface ComplianceIssue {
  description: string;
  severity: string;
  code_reference: string;
  alternatives?: any[];
}

interface VisualContent {
  id: string;
  title: string;
  description: string;
  content_type: string;
  source_document: string;
  keywords: string[];
  nz_building_codes: string[];
  trade_categories: string[];
  text_diagram?: string;
}

export default function ChatScreen() {
  const params = useLocalSearchParams();
  const initialMessage = params.message as string;
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  
  // Evidence Modal state
  const [evidenceModalVisible, setEvidenceModalVisible] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  // Handle citation click - show Evidence Modal
  const handleCitationPress = (citation: Citation) => {
    setSelectedCitation(citation);
    setEvidenceModalVisible(true);
  };

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

  const pickImage = async () => {
    try {
      // Request permissions
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'We need camera roll permissions to upload diagrams.');
        return;
      }

      // Launch image picker
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        setSelectedImage(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to select image');
    }
  };

  const sendMessageWithVision = async (messageText: string, imageUri: string) => {
    setIsLoading(true);

    try {
      // Vision endpoint not available, fallback to regular chat
      Alert.alert('Feature Not Available', 'Image analysis is not currently available. Sending your message as text instead.');
      await sendMessage(messageText || 'Please help with technical diagram analysis.');
      setSelectedImage(null);
      setInputText('');
    } catch (error) {
      console.error('Vision fallback error:', error);
      Alert.alert('Error', 'Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

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
      // Call the backend API for AI response
      const response = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText || initialMessage,
          session_id: 'mobile_app_session',
        }),
      });

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.message || "I'm still learning about NZ building codes. Can you try rephrasing your question?",
        sender: 'bot',
        timestamp: new Date(),
        citations: data.citations || [],
        confidence_score: data.confidence,
        sources_used: data.sources_used || [],
        compliance_issues: data.compliance_issues || [],
        processing_time_ms: data.timing_ms,
        visual_content: data.visual_content || [],
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

  // Handle voice input from voice controller
  const handleVoiceInput = async (voiceText: string) => {
    if (!voiceText || voiceText.trim() === '') return;
    
    setInputText(voiceText);
    setIsProcessingVoice(true);
    
    // Send the voice text as a regular message
    await sendMessage(voiceText);
    
    setIsProcessingVoice(false);
  };

  const renderMessage = (message: Message) => {
    const isUser = message.sender === 'user';
    
    return (
      <View key={message.id} style={[styles.messageContainer, isUser && styles.userMessageContainer]}>
        <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.botBubble]}>
          {/* Show uploaded image for user messages */}
          {message.image_uri && (
            <View style={styles.imageContainer}>
              <RNImage source={{ uri: message.image_uri }} style={styles.messageImage} />
              <Text style={styles.imageLabel}>📋 Technical Diagram</Text>
            </View>
          )}
          
          <Text style={[styles.messageText, isUser && styles.userMessageText]}>
            {message.text}
          </Text>
          
          {/* Vision AI indicator */}
          {message.is_vision_response && (
            <View style={styles.visionIndicator}>
              <IconSymbol name="eye.fill" size={14} color={Colors.dark.tint} />
              <Text style={styles.visionText}>Diagram Analysis</Text>
            </View>
          )}
          
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
              {message.citations.slice(0, 3).map((citation, index) => (
                <TouchableOpacity 
                  key={citation.id || citation.chunk_id || index} 
                  style={styles.citation}
                  onPress={() => handleCitationPress(citation)}
                >
                  <IconSymbol 
                    name={citation.document_type === 'nzbc' ? 'doc.text.fill' : 'building.2.fill'} 
                    size={14} 
                    color={Colors.dark.tint} 
                  />
                  <View style={styles.citationContent}>
                    <Text style={styles.citationTitle} numberOfLines={2}>
                      {citation.source || citation.title || 'Unknown Source'}
                    </Text>
                    {(citation.pages || citation.clause) && (
                      <Text style={styles.citationSnippet} numberOfLines={1}>
                        {citation.pages ? `Page: ${citation.pages}` : ''}{citation.clause ? ` • ${citation.clause}` : ''}
                      </Text>
                    )}
                  </View>
                  <IconSymbol 
                    name="chevron.right" 
                    size={12} 
                    color={Colors.dark.icon} 
                  />
                </TouchableOpacity>
              ))}
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

        {/* Input area */}
        <View style={styles.inputContainer}>
          {/* Selected Image Preview */}
          {selectedImage && (
            <View style={styles.selectedImageContainer}>
              <RNImage source={{ uri: selectedImage }} style={styles.selectedImage} />
              <Text style={styles.selectedImageText}>📋 Ready to analyze diagram</Text>
              <TouchableOpacity 
                style={styles.removeImageButton}
                onPress={() => setSelectedImage(null)}
              >
                <IconSymbol name="xmark.circle.fill" size={20} color={Colors.dark.icon} />
              </TouchableOpacity>
            </View>
          )}

          {/* Voice Controller for hands-free chat */}
          <View style={styles.voiceControllerContainer}>
            <VoiceController
              onVoiceInput={handleVoiceInput}
              isProcessing={isProcessingVoice || isLoading}
              lastResponse={messages.length > 0 && messages[messages.length - 1].sender === 'bot' 
                ? messages[messages.length - 1].text 
                : ''}
            />
          </View>
          
          <View style={styles.inputRow}>
            {/* Diagram Upload Button */}
            <TouchableOpacity
              style={styles.uploadButton}
              onPress={pickImage}
              disabled={isLoading}
            >
              <IconSymbol name="photo" size={20} color={Colors.dark.tint} />
            </TouchableOpacity>
            
            <TextInput
              style={styles.input}
              value={inputText}
              onChangeText={setInputText}
              placeholder={selectedImage ? "Ask about this diagram..." : "Ask STRYDA about building codes, products, compliance..."}
              placeholderTextColor={Colors.dark.placeholder}
              multiline
              maxLength={500}
            />
            
            <TouchableOpacity
              style={[styles.sendButton, (!inputText.trim() && !selectedImage) && styles.sendButtonDisabled]}
              onPress={() => {
                if (selectedImage) {
                  sendMessageWithVision(inputText.trim(), selectedImage);
                } else {
                  sendMessage(inputText.trim());
                }
              }}
              disabled={isLoading || (!inputText.trim() && !selectedImage)}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color={Colors.dark.background} />
              ) : (
                <IconSymbol name="paperplane.fill" size={18} color={Colors.dark.background} />
              )}
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
      
      {/* Evidence Modal */}
      <Modal
        visible={evidenceModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setEvidenceModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Source Extract / Evidence</Text>
              <TouchableOpacity 
                onPress={() => setEvidenceModalVisible(false)}
                style={styles.modalCloseButton}
              >
                <IconSymbol name="xmark.circle.fill" size={24} color={Colors.dark.icon} />
              </TouchableOpacity>
            </View>
            
            {selectedCitation && (
              <ScrollView style={styles.modalBody}>
                <View style={styles.modalSourceInfo}>
                  <Text style={styles.modalSourceTitle}>
                    {selectedCitation.source || selectedCitation.title || 'Unknown Source'}
                  </Text>
                  {(selectedCitation.pages || selectedCitation.clause || selectedCitation.section) && (
                    <Text style={styles.modalSourceMeta}>
                      {selectedCitation.pages ? `Page: ${selectedCitation.pages}` : ''}
                      {selectedCitation.clause ? ` • ${selectedCitation.clause}` : ''}
                      {selectedCitation.section ? `\n${selectedCitation.section}` : ''}
                    </Text>
                  )}
                </View>
                
                <View style={styles.modalDivider} />
                
                <Text style={styles.modalEvidenceText}>
                  {selectedCitation.text_content || selectedCitation.snippet || 'No text content available for this citation.'}
                </Text>
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
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
  selectedImageContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    gap: 12,
  },
  selectedImage: {
    width: 50,
    height: 50,
    borderRadius: 8,
  },
  selectedImageText: {
    flex: 1,
    fontSize: 14,
    color: Colors.dark.text,
    fontWeight: '500',
  },
  removeImageButton: {
    padding: 4,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: Colors.dark.inputBackground,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  uploadButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.dark.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  input: {
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
  imageContainer: {
    marginBottom: 8,
    alignItems: 'center',
  },
  messageImage: {
    width: 200,
    height: 150,
    borderRadius: 8,
    marginBottom: 4,
  },
  imageLabel: {
    fontSize: 12,
    color: Colors.dark.icon,
    fontStyle: 'italic',
  },
  visionIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.dark.border + '40',
  },
  visionText: {
    fontSize: 11,
    color: Colors.dark.tint,
    fontWeight: '500',
  },
  // Visual Content Styles
  visualContentContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.dark.border + '40',
  },
  visualContentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  visualContentTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.dark.tint,
  },
  visualContentCard: {
    backgroundColor: Colors.dark.surface + '40',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  },
  visualContentInfo: {
    flex: 1,
  },
  visualTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 4,
  },
  visualDescription: {
    fontSize: 12,
    color: Colors.dark.icon,
    marginBottom: 6,
    lineHeight: 16,
  },
  visualMetadata: {
    marginBottom: 6,
  },
  visualSource: {
    fontSize: 11,
    color: Colors.dark.tint,
    marginBottom: 2,
  },
  visualCodes: {
    fontSize: 11,
    color: Colors.dark.tint,
    fontWeight: '500',
  },
  textDiagramContainer: {
    backgroundColor: Colors.dark.background,
    borderRadius: 6,
    padding: 8,
    marginTop: 6,
    borderLeftWidth: 3,
    borderLeftColor: Colors.dark.tint,
  },
  textDiagram: {
    fontSize: 10,
    color: Colors.dark.icon,
    fontFamily: 'monospace',
    lineHeight: 14,
  },
  moreVisualsText: {
    fontSize: 11,
    color: Colors.dark.tint,
    fontStyle: 'italic',
    marginTop: 4,
    textAlign: 'center',
  },
  // Voice Controller Container
  voiceControllerContainer: {
    paddingVertical: 16,
    paddingHorizontal: 20,
    backgroundColor: Colors.dark.surface + '20',
    borderRadius: 12,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: Colors.dark.border + '30',
  },
});