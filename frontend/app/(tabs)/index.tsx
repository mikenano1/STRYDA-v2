import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { DEV_DIAG } from '../internal/diag';
import DiagOverlay from '../internal/DiagOverlay';

const theme = {
  bg: '#111111',
  text: '#FFFFFF',
  muted: '#A7A7A7',
  accent: '#FF7A00',
  inputBg: '#1A1A1A'
};

export default function HomeScreen() {
  const [searchText, setSearchText] = useState('');
  const router = useRouter();

  const handleSearch = () => {
    if (searchText.trim()) {
      // Navigate to chat with prefilled text
      router.push({
        pathname: '/chat',
        params: { prefill: searchText.trim() }
      });
    }
  };

  const goToChat = (prefillText?: string) => {
    router.push({
      pathname: '/chat',
      params: prefillText ? { prefill: prefillText } : {}
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Logo */}
      <View style={styles.logoContainer}>
        <Text style={styles.logoText}>STRYDA</Text>
        <Text style={[styles.logoText, { color: theme.accent }]}>ai</Text>
      </View>
      
      {/* Tagline */}
      <Text style={styles.tagline}>
        Your on-site co-pilot for smarter, safer builds.
      </Text>
      
      {/* Quick search */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Ask about building codes..."
          placeholderTextColor={theme.muted}
          value={searchText}
          onChangeText={setSearchText}
          onFocus={() => goToChat(searchText)}
          onSubmitEditing={handleSearch}
        />
      </View>
      
      {/* Quick actions */}
      <View style={styles.quickActions}>
        <Text style={styles.quickTitle}>Common Questions:</Text>
        
        <TouchableOpacity 
          style={styles.quickButton}
          onPress={() => goToChat('What is minimum apron flashing cover?')}
        >
          <Text style={styles.quickButtonText}>📏 Apron Flashing Cover</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.quickButton}
          onPress={() => goToChat('Nog spacings for 90mm studs in high wind?')}
        >
          <Text style={styles.quickButtonText}>🏗️ Nog Spacings</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.quickButton}
          onPress={() => goToChat('Metal roofing fastener requirements')}
        >
          <Text style={styles.quickButtonText}>🔩 Fastener Requirements</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.quickButton}
          onPress={() => goToChat('Wind zone requirements for coastal areas')}
        >
          <Text style={styles.quickButtonText}>💨 Wind Zone Requirements</Text>
        </TouchableOpacity>
      </View>
      
      {/* Diagnostic Overlay (dev only) */}
      {DEV_DIAG ? <DiagOverlay /> : null}
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
  searchContainer: {
    width: '100%',
    maxWidth: 400,
    marginBottom: 40,
  },
  searchInput: {
    backgroundColor: theme.inputBg,
    borderRadius: 24,
    paddingHorizontal: 20,
    paddingVertical: 16,
    fontSize: 16,
    color: theme.text,
    borderWidth: 2,
    borderColor: theme.accent,
  },
  quickActions: {
    width: '100%',
    maxWidth: 400,
  },
  quickTitle: {
    color: theme.text,
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  quickButton: {
    backgroundColor: theme.inputBg,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: theme.accent,
  },
  quickButtonText: {
    color: theme.text,
    fontSize: 16,
    fontWeight: '500',
  },
});