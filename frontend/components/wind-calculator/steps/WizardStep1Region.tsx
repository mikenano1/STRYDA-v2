// app/frontend/components/wind-calculator/steps/WizardStep1Region.tsx

import React, { useState, useEffect } from 'react';
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
  initialData?: RegionData; // Allow pre-filling data if navigating back
}

const WizardStep1Region: React.FC<Props> = ({ onNext, onBack, initialData }) => {
  const [region, setRegion] = useState<RegionData['region']>(initialData?.region || null);
  const [isLeeZone, setIsLeeZone] = useState<RegionData['isLeeZone']>(initialData?.isLeeZone || null);

  // Form validation: Check if all required fields are filled
  const isFormComplete = region !== null && isLeeZone !== null;

  const handleNext = () => {
    if (isFormComplete) {
      // Pass the collected data to the parent wizard
      onNext({ region, isLeeZone });
    }
  };

  // Reusable Option Button Component for consistent UI
  const OptionButton = ({ label, selected, onPress, icon, subLabel }: any) => (
    <TouchableOpacity
      style={[styles.optionBtn, selected && styles.optionBtnSelected]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.optionIconContainer}>
        <Ionicons name={icon} size={28} color={selected ? '#F97316' : '#A0A0A0'} />
      </View>
      <View style={{flex: 1}}>
        <Text style={[styles.optionText, selected && styles.optionTextSelected]}>{label}</Text>
        {subLabel && <Text style={styles.optionSubText}>{subLabel}</Text>}
      </View>
      {selected && <Ionicons name="checkmark-circle" size={28} color="#F97316" style={{ marginLeft: 10 }} />}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* SECTION 1: WIND REGION */}
        <Text style={styles.questionTitle}>1. Select Wind Region</Text>
        <Text style={styles.questionSubtitle}>Is the site in a standard or high-wind zone according to NZS 3604 Figure 5.1?</Text>
        
        <View style={styles.optionsContainer}>
          <OptionButton 
            label="Region A"
            subLabel="Most of New Zealand (Normal Wind)"
            icon="map-outline"
            selected={region === 'A'} 
            onPress={() => setRegion('A')} 
          />
          <OptionButton 
            label="Region W" 
            subLabel="Wellington, Marlborough, Lower South Island (High Wind)"
            icon="flag-outline"
            selected={region === 'W'} 
            onPress={() => setRegion('W')} 
          />
        </View>

        <View style={styles.divider} />

        {/* SECTION 2: LEE ZONES */}
        <Text style={styles.questionTitle}>2. Lee Zone Check</Text>
        <View style={styles.infoBox}>
             <Ionicons name="information-circle-outline" size={22} color="#F97316" style={{marginRight: 10}}/>
             <Text style={styles.infoText}>Sites immediately downwind of major mountain ranges can experience unpredictable, accelerated winds.</Text>
        </View>
        <Text style={[styles.questionSubtitle, {marginTop: 15}]}>Is the site located in a known Lee Zone?</Text>

        <View style={styles.optionsContainerHorizontal}>
          <TouchableOpacity 
            style={[styles.horizontalOption, isLeeZone === 'no' && styles.optionBtnSelected]}
            onPress={() => setIsLeeZone('no')}
            activeOpacity={0.7}
          >
             <Text style={[styles.horizontalText, isLeeZone === 'no' && styles.optionTextSelected]}>No</Text>
          </TouchableOpacity>

          <TouchableOpacity 
             style={[styles.horizontalOption, isLeeZone === 'unsure' && styles.optionBtnSelected]}
             onPress={() => setIsLeeZone('unsure')}
             activeOpacity={0.7}
          >
             <Text style={[styles.horizontalText, isLeeZone === 'unsure' && styles.optionTextSelected]}>Unsure</Text>
          </TouchableOpacity>

           <TouchableOpacity 
             style={[styles.horizontalOption, isLeeZone === 'yes' && styles.optionBtnSelected, { borderColor: isLeeZone === 'yes' ? '#DC2626' : '#333' }]}
             onPress={() => setIsLeeZone('yes')}
             activeOpacity={0.7}
          >
             <Text style={[styles.horizontalText, isLeeZone === 'yes' && styles.optionTextSelected, { color: isLeeZone === 'yes' ? '#DC2626' : 'white' }]}>Yes</Text>
          </TouchableOpacity>
        </View>
         
        {/* Dynamic Warning for Lee Zone = Yes */}
        {isLeeZone === 'yes' && (
          <View style={styles.sedWarningBox}>
            <Ionicons name="alert-triangle" size={20} color="#DC2626" style={{marginRight: 8}}/>
            <Text style={styles.sedWarningText}>
              <Text style={{fontWeight: 'bold'}}>Warning:</Text> 'Yes' indicates Specific Engineering Design (SED) is likely required. You may proceed, but the final calculation will reflect this requirement.
            </Text>
          </View>
        )}

      </ScrollView>

      {/* NAVIGATION FOOTER */}
      <View style={styles.footer}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <Text style={styles.backButtonText}>Exit</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.nextButton, !isFormComplete && styles.nextButtonDisabled]} 
          onPress={handleNext}
          disabled={!isFormComplete}
          activeOpacity={0.7}
        >
          <Text style={[styles.nextButtonText, !isFormComplete && styles.nextButtonTextDisabled]}>Next: Terrain</Text>
          <Ionicons name="arrow-forward" size={20} color={isFormComplete ? "white" : "#777"} style={{marginLeft: 8}}/>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  scrollContent: { padding: 20, paddingBottom: 30 },
  questionTitle: { color: 'white', fontSize: 22, fontWeight: 'bold', marginBottom: 10 },
  questionSubtitle: { color: '#A0A0A0', fontSize: 16, marginBottom: 20, lineHeight: 22 },
  optionsContainer: { marginBottom: 10 },
  optionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#171717',
    paddingVertical: 18,
    paddingHorizontal: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#222',
  },
  optionIconContainer: { marginRight: 15, width: 30, alignItems: 'center' },
  optionBtnSelected: { borderColor: '#F97316', backgroundColor: '#1F1F1F' },
  optionText: { color: 'white', fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  optionSubText: { color: '#A0A0A0', fontSize: 14 },
  optionTextSelected: { color: '#F97316' },
  divider: { height: 1, backgroundColor: '#222', marginVertical: 25 },
  infoBox: { flexDirection: 'row', backgroundColor: 'rgba(249, 115, 22, 0.1)', padding: 15, borderRadius: 8, alignItems: 'center'},
  infoText: { color: '#F97316', flex: 1, fontSize: 15, lineHeight: 20 },
  optionsContainerHorizontal: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 15 },
  horizontalOption: { flex: 1, backgroundColor: '#171717', paddingVertical: 16, borderRadius: 12, alignItems: 'center', marginHorizontal: 6, borderWidth: 2, borderColor: '#222' },
  horizontalText: { color: '#A0A0A0', fontWeight: 'bold', fontSize: 16 },
  sedWarningBox: { flexDirection: 'row', backgroundColor: 'rgba(220, 38, 38, 0.1)', padding: 15, borderRadius: 8, marginTop: 20, alignItems: 'flex-start' },
  sedWarningText: { color: '#DC2626', flex: 1, fontSize: 14, lineHeight: 20 },
  footer: { flexDirection: 'row', padding: 20, borderTopWidth: 1, borderTopColor: '#222', backgroundColor: '#0A0A0A' },
  backButton: { paddingVertical: 14, paddingHorizontal: 24, borderRadius: 8, backgroundColor: '#1F1F1F', marginRight: 12, borderWidth: 1, borderColor: '#333' },
  backButtonText: { color: 'white', fontSize: 16, fontWeight: '600' },
  nextButton: { flex: 1, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', backgroundColor: '#F97316', borderRadius: 8, paddingVertical: 14 },
  nextButtonDisabled: { backgroundColor: '#333' },
  nextButtonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  nextButtonTextDisabled: { color: '#777' },
});

export default WizardStep1Region;
