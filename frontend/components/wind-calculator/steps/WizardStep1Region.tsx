// app/frontend/components/wind-calculator/steps/WizardStep1Region.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

// Define the data structure for this step's answer
export interface RegionData {
  region: 'A' | 'W' | null;
  isLeeZone: 'yes' | 'no' | 'unsure' | null;
}

interface Props {
  onNext: (data: RegionData) => void;
  onBack: () => void;
}

const WizardStep1Region: React.FC<Props> = ({ onNext, onBack }) => {
  const [region, setRegion] = useState<RegionData['region']>(null);
  const [isLeeZone, setIsLeeZone] = useState<RegionData['isLeeZone']>(null);

  const handleNext = () => {
    if (region && isLeeZone) {
      // If Lee Zone is YES, we might need to trigger SED warning later.
      // For now, pass the data up.
      onNext({ region, isLeeZone });
    }
  };

  // Form validation
  const isFormComplete = region !== null && isLeeZone !== null;

  // Reusable Option Button Component
  const OptionButton = ({ label, selected, onPress, icon }: any) => (
    <TouchableOpacity
      style={[styles.optionBtn, selected && styles.optionBtnSelected]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Ionicons name={icon} size={24} color={selected ? 'white' : '#A0A0A0'} style={{ marginRight: 12 }} />
      <Text style={[styles.optionText, selected && styles.optionTextSelected]}>{label}</Text>
      {selected && <Ionicons name="checkmark-circle" size={24} color="#F97316" style={{ marginLeft: 'auto' }} />}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* SECTION 1: WIND REGION */}
        <Text style={styles.questionTitle}>1. Select Wind Region</Text>
        <Text style={styles.questionSubtitle}>Is the site in a standard or high-wind region?</Text>
        
        <View style={styles.optionsContainer}>
          <OptionButton 
            label="Region A (Most of NZ)" 
            icon="map-outline"
            selected={region === 'A'} 
            onPress={() => setRegion('A')} 
          />
          <OptionButton 
            label="Region W (Wellington/Marlborough/Lower South)" 
            icon="flag-outline"
            selected={region === 'W'} 
            onPress={() => setRegion('W')} 
          />
        </View>

        <View style={styles.divider} />

        {/* SECTION 2: LEE ZONES */}
        <Text style={styles.questionTitle}>2. Lee Zone Check</Text>
        <View style={styles.warningBox}>
             <Ionicons name="alert-circle-outline" size={20} color="#F97316" style={{marginRight: 8}}/>
             <Text style={styles.warningText}>Sites downwind of major mountain ranges can have unpredictable wind speeds.</Text>
        </View>
        <Text style={[styles.questionSubtitle, {marginTop: 10}]}>Is the site located in a known Lee Zone?</Text>

        <View style={styles.optionsContainerHorizontal}>
          <TouchableOpacity 
            style={[styles.horizontalOption, isLeeZone === 'no' && styles.optionBtnSelected]}
            onPress={() => setIsLeeZone('no')}
          >
             <Text style={[styles.horizontalText, isLeeZone === 'no' && styles.optionTextSelected]}>No</Text>
          </TouchableOpacity>

          <TouchableOpacity 
             style={[styles.horizontalOption, isLeeZone === 'unsure' && styles.optionBtnSelected]}
             onPress={() => setIsLeeZone('unsure')}
          >
             <Text style={[styles.horizontalText, isLeeZone === 'unsure' && styles.optionTextSelected]}>Unsure</Text>
          </TouchableOpacity>

           <TouchableOpacity 
             style={[styles.horizontalOption, isLeeZone === 'yes' && styles.optionBtnSelected, { borderColor: isLeeZone === 'yes' ? '#DC2626' : 'transparent' }]}
             onPress={() => setIsLeeZone('yes')}
          >
             <Text style={[styles.horizontalText, isLeeZone === 'yes' && styles.optionTextSelected, { color: isLeeZone === 'yes' ? '#DC2626' : '#A0A0A0' }]}>Yes</Text>
          </TouchableOpacity>
        </View>
         {isLeeZone === 'yes' && <Text style={styles.sedWarning}>⚠️ Yes indicates Specific Engineering Design (SED) may be required.</Text>}

      </ScrollView>

      {/* NAVIGATION FOOTER */}
      <View style={styles.footer}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <Text style={styles.backButtonText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.nextButton, !isFormComplete && styles.nextButtonDisabled]} 
          onPress={handleNext}
          disabled={!isFormComplete}
        >
          <Text style={[styles.nextButtonText, !isFormComplete && styles.nextButtonTextDisabled]}>Next: Terrain</Text>
          <Ionicons name="arrow-forward" size={20} color={isFormComplete ? "white" : "#555"} style={{marginLeft: 8}}/>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  scrollContent: { padding: 20 },
  questionTitle: { color: 'white', fontSize: 20, fontWeight: 'bold', marginBottom: 8 },
  questionSubtitle: { color: '#A0A0A0', fontSize: 16, marginBottom: 20 },
  optionsContainer: { marginBottom: 20 },
  optionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#171717',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  optionBtnSelected: { borderColor: '#F97316', backgroundColor: '#1F1F1F' },
  optionText: { color: '#A0A0A0', fontSize: 16, fontWeight: '600' },
  optionTextSelected: { color: 'white' },
  divider: { height: 1, backgroundColor: '#222', marginVertical: 25 },
  warningBox: { flexDirection: 'row', backgroundColor: 'rgba(249, 115, 22, 0.1)', padding: 12, borderRadius: 8, alignItems: 'center'},
  warningText: { color: '#F97316', flex: 1 },
  optionsContainerHorizontal: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 15 },
  horizontalOption: { flex: 1, backgroundColor: '#171717', padding: 16, borderRadius: 12, alignItems: 'center', marginHorizontal: 5, borderWidth: 2, borderColor: 'transparent' },
  horizontalText: { color: '#A0A0A0', fontWeight: 'bold', fontSize: 16 },
  sedWarning: { color: '#DC2626', marginTop: 10, fontStyle: 'italic' },
  footer: { flexDirection: 'row', padding: 20, borderTopWidth: 1, borderTopColor: '#222', backgroundColor: '#0A0A0A' },
  backButton: { paddingVertical: 14, paddingHorizontal: 24, borderRadius: 8, backgroundColor: '#1F1F1F', marginRight: 12 },
  backButtonText: { color: 'white', fontSize: 16, fontWeight: '600' },
  nextButton: { flex: 1, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', backgroundColor: '#F97316', borderRadius: 8, paddingVertical: 14 },
  nextButtonDisabled: { backgroundColor: '#333' },
  nextButtonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  nextButtonTextDisabled: { color: '#777' },
});

export default WizardStep1Region;
