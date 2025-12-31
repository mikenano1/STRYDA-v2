// app/frontend/components/wind-calculator/steps/WizardStep2Terrain.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

// Data interface for this step
export interface TerrainData {
  roughness: 'urban' | 'open' | 'coastal' | null;
}

interface Props {
  onNext: (data: TerrainData) => void;
  onBack: () => void;
  initialData?: TerrainData;
}

const WizardStep2Terrain: React.FC<Props> = ({ onNext, onBack, initialData }) => {
  const [roughness, setRoughness] = useState<TerrainData['roughness']>(initialData?.roughness || null);

  const handleNext = () => {
    if (roughness) {
      onNext({ roughness });
    }
  };

  // Reusable large card component for terrain types
  const TerrainCard = ({ label, subLabel, icon, selected, onPress }: any) => (
    <TouchableOpacity
      style={[styles.card, selected && styles.cardSelected]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.cardContent}>
        <Ionicons name={icon} size={40} color={selected ? '#F97316' : '#A0A0A0'} style={{ marginBottom: 10 }} />
        <Text style={[styles.cardTitle, selected && styles.cardTitleSelected]}>{label}</Text>
        <Text style={styles.cardSubtitle}>{subLabel}</Text>
      </View>
      {selected && (
        <View style={styles.checkmarkContainer}>
          <Ionicons name="checkmark-circle" size={28} color="#F97316" />
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.questionTitle}>3. Ground Roughness</Text>
        <Text style={styles.questionSubtitle}>Choose the category that best describes the land for 500m upwind of the site. Obstructions slow the wind down.</Text>

        <TerrainCard
          label="Urban / Forest"
          subLabel="Built-up areas with many obstructions (houses, trees) over 3m high."
          icon="business" // City icon
          selected={roughness === 'urban'}
          onPress={() => setRoughness('urban')}
        />

        <TerrainCard
          label="Open Country (Rural)"
          subLabel="Farm land, open spaces with few scattered obstructions."
          icon="leaf" // Leaf icon looks rural/nature
          selected={roughness === 'open'}
          onPress={() => setRoughness('open')}
        />

        <TerrainCard
          label="Coastal"
          subLabel="Near water with no significant obstructions between site and sea."
          icon="water" // Water/Waves icon
          selected={roughness === 'coastal'}
          onPress={() => setRoughness('coastal')}
        />
      </ScrollView>

      {/* NAVIGATION FOOTER */}
      <View style={styles.footer}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.nextButton, !roughness && styles.nextButtonDisabled]} 
          onPress={handleNext}
          disabled={!roughness}
          activeOpacity={0.7}
        >
          <Text style={[styles.nextButtonText, !roughness && styles.nextButtonTextDisabled]}>Next: Topography</Text>
          <Ionicons name="arrow-forward" size={20} color={roughness ? "white" : "#777"} style={{marginLeft: 8}}/>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  scrollContent: { padding: 20, paddingBottom: 30 },
  questionTitle: { color: 'white', fontSize: 22, fontWeight: 'bold', marginBottom: 10 },
  questionSubtitle: { color: '#A0A0A0', fontSize: 16, marginBottom: 25, lineHeight: 22 },
  card: {
    flexDirection: 'row',
    backgroundColor: '#171717',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#222',
    alignItems: 'center',
  },
  cardSelected: { borderColor: '#F97316', backgroundColor: '#1F1F1F' },
  cardContent: { flex: 1 },
  cardTitle: { color: 'white', fontSize: 20, fontWeight: 'bold', marginBottom: 6 },
  cardTitleSelected: { color: '#F97316' },
  cardSubtitle: { color: '#A0A0A0', fontSize: 14, lineHeight: 20 },
  checkmarkContainer: { marginLeft: 15 },
  footer: { flexDirection: 'row', padding: 20, borderTopWidth: 1, borderTopColor: '#222', backgroundColor: '#0A0A0A' },
  backButton: { paddingVertical: 14, paddingHorizontal: 24, borderRadius: 8, backgroundColor: '#1F1F1F', marginRight: 12, borderWidth: 1, borderColor: '#333' },
  backButtonText: { color: 'white', fontSize: 16, fontWeight: '600' },
  nextButton: { flex: 1, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', backgroundColor: '#F97316', borderRadius: 8, paddingVertical: 14 },
  nextButtonDisabled: { backgroundColor: '#222', borderWidth: 1, borderColor: '#333' },
  nextButtonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  nextButtonTextDisabled: { color: '#777' },
});

export default WizardStep2Terrain;
