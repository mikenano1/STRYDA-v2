// app/frontend/components/wind-calculator/StandardCalculatorWizard.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView, TouchableOpacity, Alert, LayoutAnimation, Platform, UIManager } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Council } from '../../constants/CouncilData';

// Import Steps and Data Interfaces
import WizardStep1Region, { RegionData } from './steps/WizardStep1Region';
import WizardStep2Terrain, { TerrainData } from './steps/WizardStep2Terrain';
import WizardStep3Topography, { TopographyData } from './steps/WizardStep3Topography';
import WizardStep4Shelter, { ShelterData } from './steps/WizardStep4Shelter'; // NEW
import WizardStep5Result from './steps/WizardStep5Result'; // NEW

// Import Calculation Engine
import { calculateWindZone, WindZoneResult } from '../../src/internal/utils/WindZoneEngine';

// Enable LayoutAnimation for Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface Props {
  selectedCouncil: Council;
  onExit: () => void;
}

// Master interface for all collected data
export interface CalculatorData {
  regionData?: RegionData;
  terrainData?: TerrainData;
  topographyData?: TopographyData;
  shelterData?: ShelterData;
}

const StandardCalculatorWizard: React.FC<Props> = ({ selectedCouncil, onExit }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 5; 
  const [calculatorData, setCalculatorData] = useState<CalculatorData>({});
  const [finalResult, setFinalResult] = useState<WindZoneResult | null>(null);

  // Helper to smooth transition between steps
  const advanceStep = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setCurrentStep(prev => prev + 1);
  }

  // --- STEP HANDLERS ---

  // Step 1: Region
  const handleStep1Next = (data: RegionData) => {
    setCalculatorData(prev => ({ ...prev, regionData: data }));
    advanceStep();
  };

  // Step 2: Terrain
  const handleStep2Next = (data: TerrainData) => {
    setCalculatorData(prev => ({ ...prev, terrainData: data }));
    advanceStep();
  };

  // Step 3: Topography
  const handleStep3Next = (data: TopographyData) => {
    setCalculatorData(prev => ({ ...prev, topographyData: data }));
    
    // Check if Topography forces SED (Steep)
    if (data.type === 'steep') {
        // Short-circuit to result if steep (it's SED anyway)
        // But we still need shelter data for completeness? 
        // Actually, let's just proceed to shelter to complete the picture, 
        // or jump to result if we want fail-fast. 
        // Let's proceed to shelter for consistency.
        advanceStep();
    } else {
        advanceStep();
    }
  };

  // Step 4: Shelter (Final Input)
  const handleStep4Next = (data: ShelterData) => {
    const finalData = { ...calculatorData, shelterData: data };
    setCalculatorData(finalData);
    
    // PERFORM CALCULATION
    if (finalData.regionData && finalData.terrainData && finalData.topographyData) {
        const result = calculateWindZone({
            region: finalData.regionData,
            terrain: finalData.terrainData,
            topography: finalData.topographyData,
            shelter: data
        });
        setFinalResult(result);
        advanceStep(); // Go to Step 5 (Result)
    } else {
        Alert.alert("Error", "Missing data from previous steps.");
    }
  };

  // Step 5: Result (Restart/Exit)
  const handleRestart = () => {
    setCalculatorData({});
    setFinalResult(null);
    setCurrentStep(1);
  };

  // General Back Handler
  const handleBack = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    } else {
      Alert.alert("Exit Calculator?", "Your current progress will be lost.", [
        { text: "Cancel", style: "cancel" },
        { text: "Exit", style: "destructive", onPress: onExit }
      ]);
    }
  };

  // --- RENDER CURRENT STEP ---
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <WizardStep1Region 
            onNext={handleStep1Next} 
            onBack={handleBack}
            initialData={calculatorData.regionData}
          />
        );
      case 2:
        return (
          <WizardStep2Terrain
            onNext={handleStep2Next}
            onBack={handleBack}
            initialData={calculatorData.terrainData}
          />
        );
      case 3:
        return (
          <WizardStep3Topography
            onNext={handleStep3Next}
            onBack={handleBack}
            initialData={calculatorData.topographyData}
          />
        );
      case 4:
        return (
          <WizardStep4Shelter
            onNext={handleStep4Next}
            onBack={handleBack}
            initialData={calculatorData.shelterData}
          />
        );
      case 5:
        return (
          <WizardStep5Result
            result={finalResult || 'SED Required'}
            onRestart={handleRestart}
            onExit={onExit}
          />
        );
      default:
        return <View style={styles.centerMsg}><Text style={styles.errorText}>Step implementation pending.</Text></View>;
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
       {/* Wizard Header */}
      <View style={styles.wizardHeader}>
        <View>
           <Text style={styles.councilLabel}>{selectedCouncil.name}</Text>
           <Text style={styles.headerSubtext}>NZS 3604 Calculation</Text>
        </View>
        <View style={styles.progressContainer}>
          {/* Simple visual progress bar */}
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${(currentStep / totalSteps) * 100}%` }]} />
          </View>
          <Text style={styles.stepIndicator}>Step {currentStep}/{totalSteps}</Text>
          <TouchableOpacity onPress={handleBack} style={styles.closeBtn} activeOpacity={0.7}>
             <Ionicons name="close" size={24} color="#A0A0A0" />
          </TouchableOpacity>
        </View>
      </View>
      
      <View style={styles.contentContainer}>
        {renderStep()}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  wizardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 15, paddingHorizontal: 20, borderBottomWidth: 1, borderBottomColor: '#1F1F1F', backgroundColor: '#0A0A0A' },
  councilLabel: { color: 'white', fontWeight: '700', fontSize: 16 },
  headerSubtext: { color: '#A0A0A0', fontSize: 12 },
  progressContainer: { flexDirection: 'row', alignItems: 'center' },
  progressBarBg: { width: 60, height: 6, backgroundColor: '#222', borderRadius: 3, marginRight: 10, overflow: 'hidden' },
  progressBarFill: { height: '100%', backgroundColor: '#F97316' },
  stepIndicator: { color: '#A0A0A0', fontWeight: '600', marginRight: 15, fontSize: 14 },
  closeBtn: { padding: 4 },
  contentContainer: { flex: 1 },
  centerMsg: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  errorText: { color: 'red', fontSize: 18 }
});

export default StandardCalculatorWizard;
