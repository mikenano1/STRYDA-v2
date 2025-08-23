import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Animated,
} from 'react-native';
import { router } from 'expo-router';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';

export default function VoiceScreen() {
  const [isListening, setIsListening] = useState(false);
  const [pulseAnim] = useState(new Animated.Value(1));

  const startListening = () => {
    setIsListening(true);
    
    // Start pulse animation
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }),
      ])
    );
    pulse.start();

    // Simulate voice recognition (replace with real implementation)
    setTimeout(() => {
      stopListening();
      // Navigate to chat with simulated voice input
      router.push({
        pathname: '/chat',
        params: { message: 'What are the hearth clearances for a Metrofires unit on timber floor?' }
      });
    }, 3000);
  };

  const stopListening = () => {
    setIsListening(false);
    pulseAnim.stopAnimation();
    Animated.timing(pulseAnim, {
      toValue: 1,
      duration: 200,
      useNativeDriver: true,
    }).start();
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={() => router.back()}
          >
            <IconSymbol name="chevron.left" size={20} color={Colors.dark.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Push to Talk</Text>
          <View style={styles.headerSpacer} />
        </View>

        {/* Voice indicator */}
        <View style={styles.voiceContainer}>
          <Animated.View style={[styles.micContainer, { transform: [{ scale: pulseAnim }] }]}>
            <TouchableOpacity
              style={[styles.micButton, isListening && styles.micButtonActive]}
              onPress={isListening ? stopListening : startListening}
              activeOpacity={0.8}
            >
              <IconSymbol 
                name="mic.fill" 
                size={48} 
                color={isListening ? Colors.dark.background : Colors.dark.text}
              />
            </TouchableOpacity>
          </Animated.View>

          <Text style={styles.instructionText}>
            {isListening 
              ? "Listening... Ask your question now" 
              : "Hold to ask about NZ building codes"
            }
          </Text>

          {isListening && (
            <View style={styles.waveformContainer}>
              <Text style={styles.waveformText}>🎵 Voice detected...</Text>
            </View>
          )}
        </View>

        {/* Sample questions */}
        <View style={styles.samplesContainer}>
          <Text style={styles.samplesTitle}>Try asking:</Text>
          <Text style={styles.sampleText}>"What's the minimum hearth clearance for Metrofires?"</Text>
          <Text style={styles.sampleText}>"Do I need H1 insulation in Auckland?"</Text>
          <Text style={styles.sampleText}>"What's required for E2 weathertightness?"</Text>
        </View>

        {/* Feature note */}
        <View style={styles.noteContainer}>
          <Text style={styles.noteText}>
            🚧 Voice recognition coming soon! This is a preview of the push-to-talk feature.
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.dark.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
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
  headerSpacer: {
    width: 40,
  },
  voiceContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  micContainer: {
    marginBottom: 32,
  },
  micButton: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: Colors.dark.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: Colors.dark.tint,
  },
  micButtonActive: {
    backgroundColor: Colors.dark.tint,
  },
  instructionText: {
    fontSize: 18,
    color: Colors.dark.text,
    textAlign: 'center',
    marginBottom: 20,
  },
  waveformContainer: {
    alignItems: 'center',
  },
  waveformText: {
    fontSize: 14,
    color: Colors.dark.icon,
  },
  samplesContainer: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  samplesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 12,
  },
  sampleText: {
    fontSize: 14,
    color: Colors.dark.icon,
    marginBottom: 8,
    paddingLeft: 12,
  },
  noteContainer: {
    backgroundColor: Colors.dark.surfaceSecondary,
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  noteText: {
    fontSize: 14,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 20,
  },
});