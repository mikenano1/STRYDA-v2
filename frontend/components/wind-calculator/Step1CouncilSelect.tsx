// app/frontend/components/wind-calculator/Step1CouncilSelect.tsx

import React from 'react';
import { View, Text, StyleSheet, SectionList, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NZ_COUNCILS_GROUPED, Council } from '../../constants/CouncilData';

interface Props {
  onCouncilSelect: (council: Council) => void;
}

const Step1CouncilSelect: React.FC<Props> = ({ onCouncilSelect }) => {
  // Renders the orange region header (e.g., "Auckland Region")
  const renderSectionHeader = ({ section: { title } }: any) => (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionHeaderText}>{title}</Text>
    </View>
  );

  // Renders individual council rows (e.g., "Wellington City Council")
  const renderItem = ({ item }: { item: Council }) => (
    <TouchableOpacity
      style={styles.itemContainer}
      onPress={() => onCouncilSelect(item)}
      activeOpacity={0.7}
    >
      <Text style={styles.itemText}>{item.name}</Text>
      {/* Adds a red warning badge if the council has mandatory maps */}
      {item.type === 'override' && (
        <View style={styles.overrideBadge}>
          <Text style={styles.overrideText}>Map Required</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.headerContainer}>
        <Text style={styles.headerTitle}>Step 1: Select Local Council</Text>
        <Text style={styles.headerSubtitle}>
          Select the authority for the job site. Some councils have mandatory wind maps that override calculations.
        </Text>
      </View>

      <SectionList
        sections={NZ_COUNCILS_GROUPED}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        renderSectionHeader={renderSectionHeader}
        stickySectionHeadersEnabled={true} // Headers stay at top while scrolling section
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  headerContainer: { padding: 20, paddingBottom: 15, backgroundColor: '#0A0A0A' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: 'white', marginBottom: 8 },
  headerSubtitle: { fontSize: 15, color: '#A0A0A0', lineHeight: 22 },
  listContent: { paddingBottom: 30 },
  sectionHeader: {
    backgroundColor: '#171717', // Slightly lighter dark background for contrast
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  sectionHeaderText: { color: '#F97316', fontSize: 16, fontWeight: '700', letterSpacing: 0.5 },
  itemContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 18,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#1F1F1F',
    backgroundColor: '#0A0A0A',
  },
  itemText: { color: 'white', fontSize: 17, fontWeight: '500' },
  overrideBadge: {
    backgroundColor: 'rgba(220, 38, 38, 0.2)', // Subtle red background
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#DC2626', // Solid red border
  },
  overrideText: { color: '#EF4444', fontSize: 12, fontWeight: '700' },
});

export default Step1CouncilSelect;
