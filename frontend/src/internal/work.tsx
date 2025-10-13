import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const theme = { 
  bg: '#000000', 
  text: '#FFFFFF', 
  muted: '#A7A7A7', 
  accent: '#FF7A00', 
  inputBg: '#1A1A1A' 
};

export default function ToolsScreen() {
  const tools = [
    { name: 'Pitch Calculator', description: 'Calculate roof pitch angles' },
    { name: 'Scupper Sizing', description: 'Determine proper scupper dimensions' },
    { name: 'Fastener Selector', description: 'Choose the right fasteners' },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Construction Tools</Text>
        <Text style={styles.subtitle}>(coming soon)</Text>

        {tools.map((tool, index) => (
          <View key={index} style={styles.toolCard}>
            <View style={styles.toolIconContainer}>
              <Text style={styles.toolIcon}>🔧</Text>
            </View>
            <View style={styles.toolInfo}>
              <Text style={styles.toolName}>{tool.name}</Text>
              <Text style={styles.toolDescription}>{tool.description}</Text>
            </View>
            <View style={styles.disabledBadge}>
              <Text style={styles.disabledText}>Soon</Text>
            </View>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.bg,
  },
  content: {
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: theme.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: theme.muted,
    marginBottom: 24,
  },
  toolCard: {
    flexDirection: 'row',
    backgroundColor: theme.inputBg,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333333',
    marginBottom: 12,
    alignItems: 'center',
    gap: 16,
  },
  toolIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: theme.bg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  toolIcon: {
    fontSize: 24,
  },
  toolInfo: {
    flex: 1,
  },
  toolName: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.text,
    marginBottom: 4,
  },
  toolDescription: {
    fontSize: 14,
    color: theme.muted,
  },
  disabledBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#333333',
  },
  disabledText: {
    fontSize: 12,
    color: theme.muted,
    fontWeight: '600',
  },
});
