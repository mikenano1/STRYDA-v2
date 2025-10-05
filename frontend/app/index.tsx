import React, { useState } from 'react';
import { Text, View, StyleSheet, TextInput, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const theme = { 
  bg: '#111111', 
  text: '#FFFFFF', 
  muted: '#A7A7A7', 
  accent: '#FF7A00', 
  inputBg: '#1A1A1A' 
};

export default function HomeScreen() {
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [lastResponse, setLastResponse] = useState('');
  const [citations, setCitations] = useState([]);

  const handleSend = async () => {
    if (!inputText.trim() || isSending) return;
    
    setIsSending(true);
    const message = inputText.trim();
    setInputText('');
    
    try {
      console.log('🚀 Sending chat request:', message);
      
      const response = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: 'demo_session_001',
          message: message
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      console.log('✅ Chat response:', { 
        messageLength: data.message?.length,
        citationCount: data.citations?.length 
      });
      
      setLastResponse(data.message || 'No response');
      setCitations(data.citations || []);
      
    } catch (error) {
      console.error('❌ Chat request failed:', error);
      Alert.alert('Error', 'Failed to get response from STRYDA. Please try again.');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* STRYDA Logo */}
      <View style={styles.logoContainer}>
        <Text style={styles.logoText}>STRYDA</Text>
        <Text style={[styles.logoText, { color: theme.accent }]}>ai</Text>
      </View>
      
      {/* Tagline */}
      <Text style={styles.tagline}>Your on-site co-pilot for smarter, safer builds.</Text>
      
      {/* Chat Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          placeholder="Ask me anything about NZ building codes..."
          placeholderTextColor={theme.muted}
          value={inputText}
          onChangeText={setInputText}
          multiline
          returnKeyType="send"
          onSubmitEditing={handleSend}
          editable={!isSending}
        />
        <TouchableOpacity 
          style={[
            styles.sendButton,
            isSending && styles.sendButtonDisabled
          ]} 
          onPress={handleSend}
          disabled={isSending}
        >
          <Text style={styles.sendButtonText}>
            {isSending ? '...' : 'Send'}
          </Text>
        </TouchableOpacity>
      </View>
      
      {/* Response Area */}
      {lastResponse ? (
        <View style={styles.responseContainer}>
          <Text style={styles.responseTitle}>STRYDA Response:</Text>
          <Text style={styles.responseText}>{lastResponse}</Text>
          
          {citations.length > 0 && (
            <View style={styles.citationsContainer}>
              <Text style={styles.citationsTitle}>Sources:</Text>
              {citations.map((citation, index) => (
                <View key={index} style={styles.citationPill}>
                  <Text style={styles.citationText}>
                    {citation.source} p.{citation.page}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </View>
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.bg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: theme.text,
  },
  tagline: {
    fontSize: 18,
    color: theme.muted,
    textAlign: 'center',
    marginBottom: 40,
    paddingHorizontal: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    width: '100%',
    maxWidth: 400,
    marginBottom: 20,
  },
  textInput: {
    flex: 1,
    backgroundColor: theme.inputBg,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: theme.text,
    marginRight: 12,
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: theme.accent,
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#555555',
  },
  sendButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
  },
  responseContainer: {
    width: '100%',
    maxWidth: 500,
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
  },
  responseTitle: {
    color: theme.accent,
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  responseText: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  citationsContainer: {
    marginTop: 8,
  },
  citationsTitle: {
    color: theme.muted,
    fontSize: 12,
    marginBottom: 8,
  },
  citationPill: {
    backgroundColor: theme.accent,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginRight: 8,
    marginBottom: 4,
    alignSelf: 'flex-start',
  },
  citationText: {
    color: '#000',
    fontSize: 12,
    fontWeight: '500',
  },
});
