import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

const theme = { 
  bg: '#000000', 
  text: '#FFFFFF', 
  muted: '#A7A7A7', 
  accent: '#FF7A00', 
  inputBg: '#1A1A1A' 
};

export default function HomeScreen() {
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);

  const onSend = async () => {
    if (!text.trim() || sending) return;
    setSending(true);
    try {
      // Stub - just clear input after delay
      await new Promise(resolve => setTimeout(resolve, 300));
    } finally {
      setSending(false);
      setText('');
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
          <TouchableOpacity style={styles.send} onPress={onSend} disabled={sending}>
            <Ionicons name="send" size={22} color="#fff" />
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.bg },
  centerWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 20 },
  logo: { color: theme.text, fontSize: 44, fontWeight: '800', letterSpacing: 0.5 },
  ai: { color: theme.accent },
  tagline: { color: theme.text, textAlign: 'center', fontSize: 16, marginTop: 10 },
  spacer: { height: 36 },
  chatBox: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.inputBg, borderRadius: 28, paddingHorizontal: 14, paddingVertical: Platform.select({ ios: 12, android: 8, default: 10 }), width: '100%' },
  input: { flex: 1, color: theme.text, fontSize: 16 },
  send: { marginLeft: 10, backgroundColor: theme.accent, borderRadius: 20, padding: 10 }
});
