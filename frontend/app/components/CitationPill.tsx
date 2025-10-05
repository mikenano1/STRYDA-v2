/**
 * Citation Pill Component
 * Small tappable pill showing citation source and page
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Citation } from '../types/chat';

interface CitationPillProps {
  citation: Citation;
  onPress: (citation: Citation) => void;
}

export function CitationPill({ citation, onPress }: CitationPillProps) {
  const handlePress = () => {
    console.log('📄 Citation tapped:', { source: citation.source, page: citation.page });
    onPress(citation);
  };

  return (
    <TouchableOpacity
      style={styles.pill}
      onPress={handlePress}
      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
      accessibilityLabel={`Citation from ${citation.source} page ${citation.page}`}
      accessibilityRole="button"
    >
      <Text style={styles.pillText}>
        {citation.source} p.{citation.page}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  pill: {
    backgroundColor: '#FF7A00', // Orange accent
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginRight: 6,
    marginBottom: 4,
    alignSelf: 'flex-start',
  },
  pillText: {
    color: '#000000',
    fontSize: 12,
    fontWeight: '500',
  }
});

export default CitationPill;