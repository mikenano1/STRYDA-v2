import React, { useState } from 'react';
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
} from 'react-native';
import { Colors, BrandColors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';
import { router } from 'expo-router';

const quickQuestions = [
  'Hearth clearances',
  'H1 insulation requirements',
  'E2 weathertightness',
  'Building consent process',
  'Fire rating requirements',
  'Metrofires installation',
];

export default function HomeScreen() {
  const [inputText, setInputText] = useState('');

  const handleSendMessage = () => {
    if (inputText.trim()) {
      // Navigate to chat with the message
      router.push({
        pathname: '/chat',
        params: { message: inputText.trim() }
      });
    }
  };

  const handleQuickQuestion = (question: string) => {
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
          {/* Header with logo and greeting */}
          <View style={styles.header}>
            <View style={styles.logoContainer}>
              <Image 
                source={require('@/assets/images/stryda-logo.png')} 
                style={styles.logoImage}
                resizeMode="contain"
              />
              <View style={styles.brandingContainer}>
                <Text style={styles.logoText}>STRYDA</Text>
                <Text style={styles.logoSubtext}>ai</Text>
              </View>
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

          {/* Quick actions */}
          <View style={styles.quickActions}>
            <Text style={styles.quickActionsTitle}>Quick Questions</Text>
            <View style={styles.quickActionButtons}>
              {quickQuestions.map((question, index) => (
                <TouchableOpacity 
                  key={index}
                  style={styles.quickActionButton}
                  onPress={() => handleQuickQuestion(question)}
                >
                  <Text style={styles.quickActionText}>{question}</Text>
                </TouchableOpacity>
              ))}
            </View>
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
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 60,
  },
  header: {
    alignItems: 'center',
    marginBottom: 60,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: Colors.dark.text,
    letterSpacing: -1,
  },
  logoSubtext: {
    fontSize: 24,
    fontWeight: '300',
    color: Colors.dark.tint,
    marginLeft: 4,
  },
  greeting: {
    fontSize: 16,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 22,
    maxWidth: 320,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 12,
    marginBottom: 40,
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
  quickActions: {
    marginTop: 'auto',
    paddingBottom: 40,
  },
  quickActionsTitle: {
    fontSize: 14,
    color: Colors.dark.icon,
    marginBottom: 12,
    textAlign: 'center',
  },
  quickActionButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
  },
  quickActionButton: {
    backgroundColor: Colors.dark.surface,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  quickActionText: {
    fontSize: 14,
    color: Colors.dark.text,
  },
});