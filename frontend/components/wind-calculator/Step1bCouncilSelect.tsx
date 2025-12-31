// app/frontend/components/wind-calculator/Step1bCouncilSelect.tsx

import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Council, Region } from '../../constants/CouncilData';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  region: Region;
  onCouncilSelect: (council: Council) => void;
  onBack: () => void;
}

const Step1bCouncilSelect: React.FC<Props> = ({ region, onCouncilSelect, onBack }) => {
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
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>
        <View>
          <Text style={styles.headerTitle}>{region.name}</Text>
          <Text style={styles.headerSubtitle}>
            Select the local authority from this region.
          </Text>
        </View>
      </View>

      <FlatList
        data={region.councils}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  headerContainer: { padding: 20, paddingBottom: 15, backgroundColor: '#0A0A0A', flexDirection: 'row', alignItems: 'center' },
  backButton: { marginRight: 15, padding: 5 },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: 'white', marginBottom: 4 },
  headerSubtitle: { fontSize: 15, color: '#A0A0A0' },
  listContent: { paddingBottom: 30 },
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
    backgroundColor: 'rgba(220, 38, 38, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#DC2626',
  },
  overrideText: { color: '#EF4444', fontSize: 12, fontWeight: '700' },
});

export default Step1bCouncilSelect;
