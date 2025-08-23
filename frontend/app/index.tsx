import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  Image,
  Animated,
  Easing,
} from 'react-native';
import { Colors, BrandColors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { router } from 'expo-router';

export default function HomeScreen() {
  const [inputText, setInputText] = useState('');
  const [isQuickQuestionsExpanded, setIsQuickQuestionsExpanded] = useState(false);
  const [quickQuestions, setQuickQuestions] = useState([
    'What size lintel do I need for this window?',
    'What are the fire clearance rules for a fireplace?',
    'Do I need a consent for a re-roof?',
    'Is this timber compliant with NZS 3604?',
    'What\'s the right way to install vinyl cladding?',
    'How much waterproofing is needed for a bathroom?',
    'What\'s the difference between a CCC and a CoC?',
    'What are the rules for getting a Code Compliance Certificate?',
  ]);

  const handleSendMessage = () => {
    if (inputText.trim()) {
      // Navigate to chat with the message
      router.push({
        pathname: '/chat',
        params: { message: inputText.trim() }
      });
    }
  };

  // Fetch dynamic quick questions based on user analytics
  const fetchDynamicQuestions = async () => {
    try {
      const backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/analytics/popular-questions`);
      if (response.ok) {
        const data = await response.json();
        if (data.questions && data.questions.length > 0) {
          setQuickQuestions(data.questions);
        }
      }
    } catch (error) {
      console.log('Using fallback questions - analytics not ready yet');
      // Keep current fallback questions
    }
  };

  // Load dynamic questions on component mount
  useEffect(() => {
    fetchDynamicQuestions();
  }, []);

  const handleQuickQuestion = (question: string) => {
    setInputText(question);
    setIsQuickQuestionsExpanded(false);
    // Navigate to chat with the question
    router.push({
      pathname: '/chat',
      params: { message: `Tell me about ${question} in New Zealand building code` }
    });
  };

  const handleVoicePress = () => {
    router.push('/voice');
  };

  const handleContinuousVoice = () => {
    router.push('/continuous-voice');
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardContainer}
      >
        <View style={styles.content}>
          {/* Background 3D Logo */}
          <View style={styles.backgroundLogoContainer}>
            <Image 
              source={require('@/assets/images/stryda-logo.png')} 
              style={styles.backgroundLogo}
              resizeMode="contain"
            />
          </View>

          {/* Header with branding */}
          <View style={styles.header}>
            <View style={styles.brandingContainer}>
              <Text style={styles.logoText}>STRYDA</Text>
              <Text style={styles.logoSubtext}>ai</Text>
            </View>
            <Text style={styles.greeting}>
              Your on-site co-pilot for smarter, safer builds.
            </Text>
            <Text style={styles.subGreeting}>
              Ask me anything about the NZ Building Code, manufacturer specs, or site questions, and get instant, cited answers.
            </Text>
            <Text style={styles.tagline}>
              I'm here to save you time, protect your projects, and keep you compliant, hands-free.
            </Text>
          </View>

          {/* Main input area */}
          <View style={styles.inputContainer}>
            <View style={styles.inputWrapper}>
              <TextInput
                style={styles.textInput}
                placeholder="Type your building question... I'll give you instant, cited answers"
                placeholderTextColor={Colors.dark.placeholder}
                value={inputText}
                onChangeText={setInputText}
                multiline
                maxLength={500}
                returnKeyType="send"
                onSubmitEditing={handleSendMessage}
                blurOnSubmit={false}
              />
              
              {/* Voice icons inside input */}
              <View style={styles.voiceIcons}>
                <TouchableOpacity 
                  style={styles.voiceButton}
                  onPress={handleVoicePress}
                  activeOpacity={0.7}
                >
                  <IconSymbol name="mic.fill" size={20} color={Colors.dark.tint} />
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.voiceButton}
                  onPress={handleContinuousVoice}
                  activeOpacity={0.7}
                >
                  <IconSymbol name="waveform" size={20} color={Colors.dark.tint} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Send button */}
            <TouchableOpacity 
              style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
              onPress={handleSendMessage}
              disabled={!inputText.trim()}
              activeOpacity={0.8}
            >
              <IconSymbol 
                name="paperplane.fill" 
                size={20} 
                color={inputText.trim() ? Colors.dark.background : Colors.dark.placeholder} 
              />
            </TouchableOpacity>
          </View>

          {/* Expandable Quick Questions */}
          <TouchableOpacity 
            style={styles.quickQuestionsToggle}
            onPress={() => setIsQuickQuestionsExpanded(!isQuickQuestionsExpanded)}
            activeOpacity={0.8}
          >
            <View style={styles.toggleContent}>
              <IconSymbol name="lightbulb.fill" size={16} color={Colors.dark.tint} />
              <Text style={styles.toggleText}>Quick Questions</Text>
              <IconSymbol 
                name={isQuickQuestionsExpanded ? "chevron.up" : "chevron.down"} 
                size={14} 
                color={Colors.dark.icon} 
              />
            </View>
          </TouchableOpacity>

          {isQuickQuestionsExpanded && (
            <View style={styles.quickQuestionsDropdown}>
              {quickQuestions.map((question, index) => (
                <TouchableOpacity 
                  key={index}
                  style={styles.quickQuestionItem}
                  onPress={() => handleQuickQuestion(question)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.quickQuestionText}>{question}</Text>
                </TouchableOpacity>
              ))}
              <View style={styles.adaptiveLabel}>
                <IconSymbol name="brain.head.profile" size={12} color={Colors.dark.tint} />
                <Text style={styles.adaptiveLabelText}>Questions adapt based on user searches</Text>
              </View>
            </View>
          )}
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
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 60,
    position: 'relative',
  },
  backgroundLogoContainer: {
    position: 'absolute',
    top: 80,
    right: -20,
    width: 200,
    height: 200,
    zIndex: 0,
  },
  backgroundLogo: {
    width: '100%',
    height: '100%',
    opacity: 0.08,
    transform: [
      { rotateX: '15deg' },
      { rotateY: '25deg' },
      { scale: 1.2 }
    ],
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
    zIndex: 1,
  },
  brandingContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 12,
  },
  logoText: {
    fontSize: 52,
    fontWeight: 'bold',
    color: Colors.dark.text,
    letterSpacing: -1,
    textShadowColor: Colors.dark.tint + '40',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 4,
  },
  logoSubtext: {
    fontSize: 26,
    fontWeight: '300',
    color: Colors.dark.tint,
    marginLeft: 4,
    textShadowColor: Colors.dark.tint + '30',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  greeting: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.dark.text,
    textAlign: 'center',
    lineHeight: 24,
    maxWidth: 320,
    marginBottom: 8,
  },
  subGreeting: {
    fontSize: 15,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 21,
    maxWidth: 320,
    marginBottom: 6,
  },
  tagline: {
    fontSize: 14,
    color: Colors.dark.tint,
    textAlign: 'center',
    lineHeight: 20,
    maxWidth: 320,
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 12,
    marginBottom: 30,
    marginTop: 20,
    zIndex: 1,
  },
  inputWrapper: {
    flex: 1,
    backgroundColor: Colors.dark.inputBackground,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: Colors.dark.border,
    paddingHorizontal: 16,
    paddingVertical: 12,
    minHeight: 48,
    maxHeight: 120,
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: Colors.dark.text,
    marginRight: 8,
  },
  voiceIcons: {
    flexDirection: 'row',
    gap: 8,
  },
  voiceButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: Colors.dark.surface,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.dark.tint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: Colors.dark.surface,
  },
  scannerSection: {
    marginBottom: 24,
  },
  scannerButton: {
    backgroundColor: '#ff9f40', // Use the construction orange directly
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 8,
  },
  scannerButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  scannerTextContainer: {
    flex: 1,
  },
  scannerButtonTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.dark.background,
    marginBottom: 4,
  },
  scannerButtonSubtitle: {
    fontSize: 14,
    color: Colors.dark.background + '80',
    lineHeight: 18,
  },
  // Expandable Quick Questions Styles
  quickQuestionsToggle: {
    marginTop: 16,
    backgroundColor: Colors.dark.surface + '60',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.dark.border + '40',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  toggleContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  toggleText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
    color: Colors.dark.text,
    marginLeft: 8,
  },
  quickQuestionsDropdown: {
    backgroundColor: Colors.dark.surface + '40',
    borderRadius: 12,
    marginTop: 8,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: Colors.dark.border + '30',
  },
  quickQuestionItem: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.dark.border + '20',
  },
  quickQuestionText: {
    fontSize: 14,
    color: Colors.dark.text,
    lineHeight: 20,
  },
  adaptiveLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 12,
    paddingHorizontal: 16,
    gap: 6,
  },
  adaptiveLabelText: {
    fontSize: 11,
    color: Colors.dark.tint,
    fontStyle: 'italic',
  },
});