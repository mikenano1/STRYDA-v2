// app/frontend/components/wind-calculator/Step1RegionSelect.tsx

import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NZ_REGIONS, Region } from '../../constants/CouncilData';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  onRegionSelect: (region: Region) => void;
}

const Step1RegionSelect: React.FC<Props> = ({ onRegionSelect }) => {
  const renderItem = ({ item }: { item: Region }) => (
    <TouchableOpacity
      style={styles.itemContainer}
      onPress={() => onRegionSelect(item)}
      activeOpacity={0.7}
    >
      <Text style={styles.itemText}>{item.name}</Text>
      <Ionicons name="chevron-forward" size={24} color="#A0A0A0" />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.headerContainer}>
        <Text style={styles.headerTitle}>Select Region</Text>
        <Text style={styles.headerSubtitle}>
          Start by selecting the region where the job site is located.
        </Text>
      </View>

      <FlatList
        data={NZ_REGIONS}
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
  headerContainer: { padding: 20, paddingBottom: 15, backgroundColor: '#0A0A0A' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: 'white', marginBottom: 8 },
  headerSubtitle: { fontSize: 15, color: '#A0A0A0', lineHeight: 22 },
  listContent: { paddingBottom: 30 },
  itemContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#1F1F1F',
    backgroundColor: '#0A0A0A',
  },
  itemText: { color: 'white', fontSize: 18, fontWeight: '500' },
});

export default Step1RegionSelect;
