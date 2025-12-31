// app/frontend/components/wind-calculator/steps/WizardStep3Topography.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

// Data interface
export interface TopographyData {
  type: 'flat' | 'hill' | 'steep' | null;
}

interface Props {
  onNext: (data: TopographyData) => void;
  onBack: () => void;
  initialData?: TopographyData;
}

const WizardStep3Topography: React.FC<Props> = ({ onNext, onBack, initialData }) => {
  const [type, setType] = useState<TopographyData['type']>(initialData?.type || null);

  const handleNext = () => {
    if (type) {
      onNext({ type });
    }
  };

  const TopoCard = ({ label, subLabel, icon, selected, onPress, isWarning }: any) => (
    <TouchableOpacity
      style={[
        styles.card, 
        selected && styles.cardSelected,
        isWarning && selected && styles.cardWarning
      ]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.cardContent}>
        {/* Using simple icons to represent slope visually */}
        <Ionicons name={icon} size={40} color={selected ? (isWarning ? '#DC2626' : '#F97316') : '#A0A0A0'} style={{ marginBottom: 10 }} />
        <Text style={[
          styles.cardTitle, 
          selected && styles.cardTitleSelected,
          isWarning && selected && { color: '#DC2626' }
        ]}>{label}</Text>
        <Text style={styles.cardSubtitle}>{subLabel}</Text>
      </View>
      {selected && (
        <View style={styles.checkmarkContainer}>
          <Ionicons name="checkmark-circle" size={28} color={isWarning ? '#DC2626' : '#F97316'} />
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.questionTitle}>4. Topography</Text>
        <Text style={styles.questionSubtitle}>How steep is the land where the building sits? This affects wind speed-up.</Text>

        <TopoCard
          label="Flat / Gentle"
          subLabel="Slope is less than 1:20 (under 3°). Most standard subdivisions."
          icon="arrow-forward" // Flat arrow
          selected={type === 'flat'}
          onPress={() => setType('flat')}
        />

        <TopoCard
          label="Hill / Slope"
          subLabel="Significant slope (between 3° and 18°). Typical hillside property."
          icon="trending-up" // Upward arrow
          selected={type === 'hill'}
          onPress={() => setType('hill')}
        />

        <TopoCard
          label="Steep / Cliff"
          subLabel="Very steep slope (over 18°) or near a cliff edge. Warning: May require SED."
          icon="alert-circle" // Alert icon
          selected={type === 'steep'}
          onPress={() => setType('steep')}
          isWarning={true}
        />

        {type === 'steep' && (
          <View style={styles.warningBox}>
            <Text style={styles.warningText}>
              ⚠️ Zones on steep slopes often exceed NZS 3604 limits. Specific Engineering Design (SED) is highly likely.
            </Text>
          </View>
        )}

      </ScrollView>

      {/* NAVIGATION FOOTER */}
      <View style={styles.footer}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.nextButton, !type && styles.nextButtonDisabled]} 
          onPress={handleNext}
          disabled={!type}
          activeOpacity={0.7}
        >
          <Text style={[styles.nextButtonText, !type && styles.nextButtonTextDisabled]}>Next: Shielding</Text>
          <Ionicons name="arrow-forward" size={20} color={type ? "white" : "#777"} style={{marginLeft: 8}}/>
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
  cardWarning: { borderColor: '#DC2626', backgroundColor: 'rgba(220, 38, 38, 0.1)' },
  cardContent: { flex: 1 },
  cardTitle: { color: 'white', fontSize: 20, fontWeight: 'bold', marginBottom: 6 },
  cardTitleSelected: { color: '#F97316' },
  cardSubtitle: { color: '#A0A0A0', fontSize: 14, lineHeight: 20 },
  checkmarkContainer: { marginLeft: 15 },
  warningBox: { backgroundColor: 'rgba(220, 38, 38, 0.1)', padding: 15, borderRadius: 12, marginTop: 10 },
  warningText: { color: '#EF4444', fontWeight: 'bold' },
  footer: { flexDirection: 'row', padding: 20, borderTopWidth: 1, borderTopColor: '#222', backgroundColor: '#0A0A0A' },
  backButton: { paddingVertical: 14, paddingHorizontal: 24, borderRadius: 8, backgroundColor: '#1F1F1F', marginRight: 12, borderWidth: 1, borderColor: '#333' },
  backButtonText: { color: 'white', fontSize: 16, fontWeight: '600' },
  nextButton: { flex: 1, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', backgroundColor: '#F97316', borderRadius: 8, paddingVertical: 14 },
  nextButtonDisabled: { backgroundColor: '#222', borderWidth: 1, borderColor: '#333' },
  nextButtonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  nextButtonTextDisabled: { color: '#777' },
});

export default WizardStep3Topography;
