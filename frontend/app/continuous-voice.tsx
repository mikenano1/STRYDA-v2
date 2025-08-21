import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
} from 'react-native';
import { router } from 'expo-router';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';

export default function ContinuousVoiceScreen() {
  const [isActive, setIsActive] = useState(false);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={() => router.back()}
          >
            <IconSymbol name="chevron.left" size={20} color={Colors.dark.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Voice Mode</Text>
          <View style={styles.headerSpacer} />
        </View>

        {/* Voice mode info */}
        <View style={styles.infoContainer}>
          <View style={styles.logoContainer}>
            <IconSymbol name="waveform" size={64} color={Colors.dark.tint} />
          </View>
          
          <Text style={styles.title}>Continuous Voice Chat</Text>
          <Text style={styles.description}>
            Have a natural conversation with STRYDA about NZ building codes. 
            Perfect for hands-free use on construction sites.
          </Text>
        </View>

        {/* Features */}
        <View style={styles.featuresContainer}>
          <Text style={styles.featuresTitle}>Coming Soon:</Text>
          
          <View style={styles.feature}>
            <IconSymbol name="mic.fill" size={20} color={Colors.dark.success} />
            <Text style={styles.featureText}>Natural NZ accent recognition</Text>
          </View>
          
          <View style={styles.feature}>
            <IconSymbol name="waveform" size={20} color={Colors.dark.success} />
            <Text style={styles.featureText}>Continuous conversation flow</Text>
          </View>
          
          <View style={styles.feature}>
            <IconSymbol name="checkmark.circle.fill" size={20} color={Colors.dark.success} />
            <Text style={styles.featureText}>Tradie lingo understanding</Text>
          </View>
          
          <View style={styles.feature}>
            <IconSymbol name="gearshape.fill" size={20} color={Colors.dark.success} />
            <Text style={styles.featureText}>Hands-free operation</Text>
          </View>
        </View>

        {/* Voice samples */}
        <View style={styles.samplesContainer}>
          <Text style={styles.samplesTitle}>Example Conversation:</Text>
          
          <View style={styles.conversation}>
            <View style={styles.userMessage}>
              <Text style={styles.messageText}>
                "What's the clearance for a Metrofires unit?"
              </Text>
            </View>
            
            <View style={styles.botMessage}>
              <Text style={styles.messageText}>
                "For Metrofires on timber floors, you need 200mm clearance to sides, 
                400mm to front, and 50mm to rear walls. I'll send you the NZBC reference."
              </Text>
            </View>
            
            <View style={styles.userMessage}>
              <Text style={styles.messageText}>
                "What about for concrete floors?"
              </Text>
            </View>
            
            <View style={styles.botMessage}>
              <Text style={styles.messageText}>
                "On concrete floors, you can reduce the hearth to 300mm in front. 
                Side clearances remain the same at 200mm."
              </Text>
            </View>
          </View>
        </View>

        {/* Action button */}
        <TouchableOpacity 
          style={styles.actionButton}
          onPress={() => {
            // For now, navigate to regular chat
            router.push('/chat');
          }}
        >
          <Text style={styles.actionButtonText}>Try Text Chat Instead</Text>
        </TouchableOpacity>

        {/* Note */}
        <View style={styles.noteContainer}>
          <Text style={styles.noteText}>
            🎙️ Voice mode will support NZ accents and tradie terminology for natural, 
            hands-free conversations on building sites.
          </Text>
        </View>
      </ScrollView>
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
  infoContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  logoContainer: {
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.dark.text,
    marginBottom: 12,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 22,
    maxWidth: 300,
  },
  featuresContainer: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 24,
  },
  featuresTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 16,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  featureText: {
    fontSize: 14,
    color: Colors.dark.text,
    flex: 1,
  },
  samplesContainer: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 24,
  },
  samplesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    marginBottom: 16,
  },
  conversation: {
    gap: 12,
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: Colors.dark.tint,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    maxWidth: '80%',
  },
  botMessage: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.dark.surfaceSecondary,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    maxWidth: '80%',
  },
  messageText: {
    fontSize: 14,
    color: Colors.dark.text,
    lineHeight: 18,
  },
  actionButton: {
    backgroundColor: Colors.dark.tint,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 24,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.background,
  },
  noteContainer: {
    backgroundColor: Colors.dark.surfaceSecondary,
    borderRadius: 8,
    padding: 16,
    marginBottom: 32,
  },
  noteText: {
    fontSize: 14,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 20,
  },
});