import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { theme } from '../theme';

export default function LibraryScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Product Library</Text>
        <Text style={styles.subtitle}>(coming soon)</Text>
        
        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            Browse by Brand, Supplier, Category
          </Text>
        </View>

        <View style={styles.filtersContainer}>
          <Text style={styles.filtersTitle}>Filters (disabled)</Text>
          <View style={styles.filterRow}>
            <View style={[styles.filterChip, styles.filterChipDisabled]}>
              <Text style={styles.filterChipText}>Brand</Text>
            </View>
            <View style={[styles.filterChip, styles.filterChipDisabled]}>
              <Text style={styles.filterChipText}>Supplier</Text>
            </View>
            <View style={[styles.filterChip, styles.filterChipDisabled]}>
              <Text style={styles.filterChipText}>Category</Text>
            </View>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.bg,
  },
  content: {
    flex: 1,
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
  infoBox: {
    backgroundColor: theme.inputBg,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333333',
    marginBottom: 24,
  },
  infoText: {
    fontSize: 16,
    color: theme.text,
    lineHeight: 24,
  },
  filtersContainer: {
    backgroundColor: theme.inputBg,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333333',
  },
  filtersTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.muted,
    marginBottom: 12,
  },
  filterRow: {
    flexDirection: 'row',
    gap: 12,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: theme.accent,
  },
  filterChipDisabled: {
    backgroundColor: '#333333',
  },
  filterChipText: {
    fontSize: 14,
    color: theme.muted,
  },
});
