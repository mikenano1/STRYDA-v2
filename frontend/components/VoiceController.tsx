import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Animated,
  Vibration,
  Platform,
} from 'react-native';
import * as Speech from 'expo-speech';
// TODO: Re-enable @react-native-voice/voice once custom dev client is built
// import Voice from '@react-native-voice/voice';

// Voice module placeholder stubs for Expo Go compatibility
const Voice = {
  start: async () => console.log("Voice.start disabled in Expo Go"),
  stop: async () => console.log("Voice.stop disabled in Expo Go"),
  destroy: async () => console.log("Voice.destroy disabled in Expo Go"),
  cancel: async () => console.log("Voice.cancel disabled in Expo Go"),
  onSpeechStart: null,
  onSpeechRecognized: null,
  onSpeechEnd: null,
  onSpeechError: null,
  onSpeechResults: null,
  onSpeechPartialResults: null,
  onSpeechVolumeChanged: null,
  removeAllListeners: () => console.log("Voice.removeAllListeners disabled"),
  isAvailable: async () => false,
  isRecognizing: async () => false,
};

import { IconSymbol } from '@/components/ui/IconSymbol';
import { Colors } from '@/constants/Colors';

interface VoiceControllerProps {
  onVoiceInput: (text: string) => void;
  onResponse?: (response: string) => void;
  isProcessing?: boolean;
  lastResponse?: string;
}

export const VoiceController: React.FC<VoiceControllerProps> = ({
  onVoiceInput,
  onResponse,
  isProcessing = false,
  lastResponse = ''
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceText, setVoiceText] = useState('');
  const [error, setError] = useState('');
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [isWebPlatform, setIsWebPlatform] = useState(Platform.OS === 'web');
  
  const pulseAnimation = useRef(new Animated.Value(1)).current;
  const glowAnimation = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    initializeVoice();
    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
      Speech.stop();
    };
  }, []);

  // Auto-speak responses when they arrive
  useEffect(() => {
    if (lastResponse && isVoiceEnabled && !isProcessing) {
      speakResponse(lastResponse);
    }
  }, [lastResponse, isVoiceEnabled, isProcessing]);

  const initializeVoice = async () => {
    if (isWebPlatform) {
      // Web platform - use Web Speech API if available
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        console.log('Web Speech API available');
      } else {
        setError('Voice recognition not available in this browser');
      }
      return;
    }

    // Native platform - use React Native Voice
    try {
      Voice.onSpeechStart = onSpeechStart;
      Voice.onSpeechRecognized = onSpeechRecognized;
      Voice.onSpeechEnd = onSpeechEnd;
      Voice.onSpeechError = onSpeechError;
      Voice.onSpeechResults = onSpeechResults;
      Voice.onSpeechPartialResults = onSpeechPartialResults;
    } catch (e) {
      console.error('Voice initialization error:', e);
      setError('Voice not available on this device');
    }
  };

  const onSpeechStart = () => {
    setIsListening(true);
    setError('');
    Vibration.vibrate(50); // Short vibration feedback
    startPulseAnimation();
  };

  const onSpeechRecognized = () => {
    // Speech recognized but not yet processed
  };

  const onSpeechEnd = () => {
    setIsListening(false);
    stopPulseAnimation();
  };

  const onSpeechError = (e: any) => {
    console.error('Speech error:', e);
    setError(e.error?.message || 'Voice recognition error');
    setIsListening(false);
    stopPulseAnimation();
  };

  const onSpeechResults = (e: any) => {
    const results = e.value || [];
    if (results.length > 0) {
      const recognizedText = results[0];
      setVoiceText(recognizedText);
      onVoiceInput(recognizedText);
      
      // Quick success vibration
      Vibration.vibrate([50, 100, 50]);
    }
  };

  const onSpeechPartialResults = (e: any) => {
    const results = e.value || [];
    if (results.length > 0) {
      setVoiceText(results[0]);
    }
  };

  const startListening = async () => {
    try {
      setError('');
      setVoiceText('');
      
      if (isWebPlatform) {
        // Web browser - show helpful message
        Alert.alert(
          'Voice Feature',
          'Voice recognition works best on mobile devices with Expo Go app. For web testing, you can still type your questions in the chat.',
          [{ text: 'OK' }]
        );
        return;
      }
      
      // Native platform
      await Speech.stop();
      setIsSpeaking(false);
      
      await Voice.start('en-NZ'); // New Zealand English
    } catch (e) {
      console.error('Start listening error:', e);
      setError('Could not start voice recognition');
    }
  };

  const stopListening = async () => {
    try {
      await Voice.stop();
      setIsListening(false);
      stopPulseAnimation();
    } catch (e) {
      console.error('Stop listening error:', e);
    }
  };

  const speakResponse = async (text: string) => {
    try {
      if (isWebPlatform) {
        // Web platform - show message about mobile functionality
        console.log('Text-to-speech available on mobile devices');
        return;
      }

      // Native platform
      await Speech.stop();
      
      setIsSpeaking(true);
      
      // Clean the text for better speech (remove markdown, excessive punctuation)
      const cleanText = text
        .replace(/\*\*/g, '') // Remove bold markdown
        .replace(/\*/g, '') // Remove italic markdown
        .replace(/#{1,6}\s/g, '') // Remove headers
        .replace(/\[.*?\]\(.*?\)/g, '') // Remove links
        .replace(/\n+/g, '. ') // Replace line breaks with pauses
        .replace(/\.{2,}/g, '.') // Multiple dots to single
        .trim();

      await Speech.speak(cleanText, {
        language: 'en-NZ', // New Zealand English accent
        pitch: 1.0,
        rate: 0.9, // Slightly slower for better comprehension on-site
        voice: 'en-nz-x-tfm-local', // Male NZ voice if available
        onStart: () => {
          setIsSpeaking(true);
          startGlowAnimation();
        },
        onDone: () => {
          setIsSpeaking(false);
          stopGlowAnimation();
        },
        onStopped: () => {
          setIsSpeaking(false);
          stopGlowAnimation();
        },
        onError: () => {
          setIsSpeaking(false);
          stopGlowAnimation();
        }
      });
    } catch (e) {
      console.error('Speech error:', e);
      setIsSpeaking(false);
      setError('Could not speak response');
    }
  };

  const stopSpeaking = async () => {
    try {
      await Speech.stop();
      setIsSpeaking(false);
      stopGlowAnimation();
    } catch (e) {
      console.error('Stop speaking error:', e);
    }
  };

  const toggleVoiceMode = () => {
    const newState = !isVoiceEnabled;
    setIsVoiceEnabled(newState);
    
    if (newState) {
      // Speak welcome message
      speakResponse("Voice mode activated. Ask me anything about New Zealand building codes and I'll respond with voice.");
      Vibration.vibrate([100, 50, 100]); // Success pattern
    } else {
      // Stop all voice activities
      stopListening();
      stopSpeaking();
      Vibration.vibrate(200); // Single long vibration for deactivation
    }
  };

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnimation, {
          toValue: 1.3,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnimation, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const stopPulseAnimation = () => {
    pulseAnimation.stopAnimation();
    Animated.timing(pulseAnimation, {
      toValue: 1,
      duration: 200,
      useNativeDriver: true,
    }).start();
  };

  const startGlowAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnimation, {
          toValue: 1,
          duration: 800,
          useNativeDriver: false,
        }),
        Animated.timing(glowAnimation, {
          toValue: 0,
          duration: 800,
          useNativeDriver: false,
        }),
      ])
    ).start();
  };

  const stopGlowAnimation = () => {
    glowAnimation.stopAnimation();
    Animated.timing(glowAnimation, {
      toValue: 0,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  const handleMicrophonePress = () => {
    if (!isVoiceEnabled) {
      Alert.alert(
        'Voice Mode Disabled',
        'Enable voice mode first to use speech recognition.',
        [{ text: 'OK' }]
      );
      return;
    }

    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <View style={styles.container}>
      {/* Voice Mode Toggle */}
      <TouchableOpacity
        style={[
          styles.voiceModeButton,
          isVoiceEnabled && styles.voiceModeButtonActive
        ]}
        onPress={toggleVoiceMode}
        activeOpacity={0.8}
      >
        <IconSymbol 
          name={isVoiceEnabled ? "speaker.wave.3.fill" : "speaker.slash.fill"} 
          size={20} 
          color={isVoiceEnabled ? Colors.dark.background : Colors.dark.icon} 
        />
        <Text style={[
          styles.voiceModeText,
          isVoiceEnabled && styles.voiceModeTextActive
        ]}>
          {isVoiceEnabled ? 'Voice ON' : 'Voice OFF'}
        </Text>
      </TouchableOpacity>

      {isVoiceEnabled && (
        <View style={styles.voiceControls}>
          {/* Microphone Button */}
          <Animated.View style={[
            styles.micButtonContainer,
            { transform: [{ scale: pulseAnimation }] }
          ]}>
            <TouchableOpacity
              style={[
                styles.micButton,
                isListening && styles.micButtonActive,
                isProcessing && styles.micButtonProcessing
              ]}
              onPress={handleMicrophonePress}
              disabled={isProcessing}
              activeOpacity={0.8}
            >
              <IconSymbol 
                name={isListening ? "mic.fill" : "mic"} 
                size={28} 
                color={
                  isProcessing 
                    ? Colors.dark.icon 
                    : isListening 
                      ? Colors.dark.background 
                      : Colors.dark.text
                } 
              />
            </TouchableOpacity>
          </Animated.View>

          {/* Speaker Button */}
          <Animated.View style={[
            styles.speakerButtonContainer,
            { 
              borderColor: glowAnimation.interpolate({
                inputRange: [0, 1],
                outputRange: [Colors.dark.border, Colors.dark.tint + '80']
              })
            }
          ]}>
            <TouchableOpacity
              style={[
                styles.speakerButton,
                isSpeaking && styles.speakerButtonActive
              ]}
              onPress={isSpeaking ? stopSpeaking : () => speakResponse(lastResponse)}
              disabled={!lastResponse || isProcessing}
              activeOpacity={0.8}
            >
              <IconSymbol 
                name={isSpeaking ? "speaker.slash" : "speaker.wave.3"} 
                size={24} 
                color={isSpeaking ? Colors.dark.background : Colors.dark.text} 
              />
            </TouchableOpacity>
          </Animated.View>

          {/* Voice Status */}
          <View style={styles.statusContainer}>
            {isListening && (
              <View style={styles.statusItem}>
                <IconSymbol name="waveform" size={16} color={Colors.dark.tint} />
                <Text style={styles.statusText}>Listening...</Text>
              </View>
            )}
            
            {isSpeaking && (
              <View style={styles.statusItem}>
                <IconSymbol name="speaker.wave.2" size={16} color={Colors.dark.tint} />
                <Text style={styles.statusText}>Speaking...</Text>
              </View>
            )}
            
            {isProcessing && (
              <View style={styles.statusItem}>
                <IconSymbol name="brain.head.profile" size={16} color={Colors.dark.tint} />
                <Text style={styles.statusText}>Processing...</Text>
              </View>
            )}

            {voiceText && !isProcessing && (
              <Text style={styles.voiceText} numberOfLines={2}>
                "{voiceText}"
              </Text>
            )}

            {error && (
              <Text style={styles.errorText}>{error}</Text>
            )}
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    gap: 16,
  },
  voiceModeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.dark.surface,
    borderWidth: 1,
    borderColor: Colors.dark.border,
    gap: 8,
  },
  voiceModeButtonActive: {
    backgroundColor: Colors.dark.tint,
    borderColor: Colors.dark.tint,
  },
  voiceModeText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.dark.icon,
  },
  voiceModeTextActive: {
    color: Colors.dark.background,
  },
  voiceControls: {
    alignItems: 'center',
    gap: 16,
    width: '100%',
  },
  micButtonContainer: {
    shadowColor: Colors.dark.tint,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
  micButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.dark.surface,
    borderWidth: 3,
    borderColor: Colors.dark.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  micButtonActive: {
    backgroundColor: Colors.dark.tint,
    borderColor: Colors.dark.tint,
  },
  micButtonProcessing: {
    backgroundColor: Colors.dark.icon + '40',
    borderColor: Colors.dark.icon,
  },
  speakerButtonContainer: {
    borderWidth: 2,
    borderRadius: 30,
    borderColor: Colors.dark.border,
  },
  speakerButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.dark.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  speakerButtonActive: {
    backgroundColor: Colors.dark.tint,
  },
  statusContainer: {
    alignItems: 'center',
    gap: 8,
    minHeight: 60,
    justifyContent: 'center',
  },
  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusText: {
    fontSize: 14,
    color: Colors.dark.tint,
    fontWeight: '500',
  },
  voiceText: {
    fontSize: 14,
    color: Colors.dark.text,
    textAlign: 'center',
    fontStyle: 'italic',
    maxWidth: 280,
    marginTop: 4,
  },
  errorText: {
    fontSize: 12,
    color: '#ff6b6b',
    textAlign: 'center',
    maxWidth: 280,
  },
});