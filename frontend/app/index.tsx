import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { ask } from '../src/api/chatClient';

const theme = { 
  bg: '#000000', 
  text: '#FFFFFF', 
  muted: '#A7A7A7', 
  accent: '#FF7A00', 
  inputBg: '#1A1A1A' 
};

// Web Speech Recognition types
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export default function HomeScreen() {
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceAvailable, setVoiceAvailable] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);

  useEffect(() => {
    // Check for Web Speech API availability
    if (Platform.OS === 'web') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = false;
        recognitionInstance.interimResults = true;
        
        recognitionInstance.onresult = (event: any) => {
          const transcript = Array.from(event.results)
            .map((result: any) => result[0])
            .map((result: any) => result.transcript)
            .join('');
          setText(transcript);
        };
        
        recognitionInstance.onend = () => {
          setIsListening(false);
        };
        
        recognitionInstance.onerror = () => {
          setIsListening(false);
        };
        
        setRecognition(recognitionInstance);
        setVoiceAvailable(true);
      }
    }
  }, []);

  const onSend = async () => {
    if (!text.trim() || sending) return;
    setSending(true);
    try {
      // Call backend or fallback
      await ask(text.trim());
      setText('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  const toggleVoice = () => {
    if (!voiceAvailable) return;
    
    if (isListening && recognition) {
      recognition.stop();
      setIsListening(false);
    } else if (recognition) {
      recognition.start();
      setIsListening(true);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.centerWrap}>
        <View style={styles.logoContainer}>
          <View style={styles.logoBox}>
            <Text style={styles.logoLetter}>S</Text>
          </View>
          <Text style={styles.logoText}>STRYDA</Text>
        </View>
        <Text style={styles.tagline}>Your on-site co-pilot for smarter, safer builds.</Text>
        <View style={styles.spacer} />
        <View style={styles.chatBox}>
          <TextInput
            style={styles.input}
            placeholder="Ask me anything"
            placeholderTextColor={theme.muted}
            value={text}
            onChangeText={setText}
            returnKeyType="send"
            onSubmitEditing={onSend}
          />
          <TouchableOpacity 
            style={[
              styles.micButton,
              !voiceAvailable && styles.micButtonDisabled,
              isListening && styles.micButtonActive
            ]} 
            onPress={toggleVoice}
            disabled={!voiceAvailable}
            accessibilityLabel={voiceAvailable ? "Voice input" : "Voice coming soon"}
            accessibilityHint={voiceAvailable ? "Tap to start voice input" : "Voice input not available"}
          >
            <Ionicons 
              name={isListening ? "mic" : "mic-outline"} 
              size={22} 
              color="#fff" 
            />
          </TouchableOpacity>
          <TouchableOpacity style={styles.send} onPress={onSend} disabled={sending}>
            <Ionicons name="send" size={22} color="#fff" />
          </TouchableOpacity>
        </View>
        {!voiceAvailable && (
          <Text style={styles.voiceHint}>Voice coming soon</Text>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.bg },
  centerWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 20 },
  logoContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  logoBox: { 
    width: 64, 
    height: 64, 
    borderRadius: 16, 
    backgroundColor: theme.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  logoLetter: { 
    fontSize: 36, 
    fontWeight: '900', 
    color: '#FFFFFF',
  },
  logoText: { 
    fontSize: 32, 
    fontWeight: '800', 
    color: theme.text,
    letterSpacing: 1,
  },
  tagline: { color: theme.text, textAlign: 'center', fontSize: 16, marginTop: 8 },
  spacer: { height: 36 },
  chatBox: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: theme.inputBg, 
    borderRadius: 28, 
    paddingHorizontal: 14, 
    paddingVertical: Platform.select({ ios: 12, android: 8, default: 10 }), 
    width: '100%' 
  },
  input: { flex: 1, color: theme.text, fontSize: 16 },
  micButton: { 
    marginLeft: 10, 
    backgroundColor: theme.accent, 
    borderRadius: 20, 
    padding: 10,
    opacity: 1,
  },
  micButtonDisabled: {
    backgroundColor: '#333333',
    opacity: 0.5,
  },
  micButtonActive: {
    backgroundColor: '#FF0000',
  },
  send: { marginLeft: 10, backgroundColor: theme.accent, borderRadius: 20, padding: 10 },
  voiceHint: {
    color: theme.muted,
    fontSize: 12,
    marginTop: 8,
    fontStyle: 'italic',
  },
});
