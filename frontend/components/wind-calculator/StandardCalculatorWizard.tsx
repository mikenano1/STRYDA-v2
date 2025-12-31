// app/frontend/components/wind-calculator/StandardCalculatorWizard.tsx

import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, SafeAreaView, TouchableOpacity, Alert, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Council } from '../../constants/CouncilData';

// --- IMPORTS: UI STEPS ---
import WizardStep1Region, { RegionData } from './steps/WizardStep1Region';
import WizardStep2Terrain, { TerrainData } from './steps/WizardStep2Terrain';
import WizardStep3Topography, { TopographyData } from './steps/WizardStep3Topography';
import WizardStep4Shelter, { ShelterData } from './steps/WizardStep4Shelter';
import WizardStep5Result from './steps/WizardStep5Result';

// --- IMPORT: LOGIC ENGINE ---
import { calculateWindZone, WindZoneResult } from '../../src/internal/utils/WindZoneEngine';

interface Props {
  selectedCouncil: Council;
  onExit: () => void;
}

export interface CalculatorData {
  regionData?: RegionData;
  terrainData?: TerrainData;
  topographyData?: TopographyData;
  shelterData?: ShelterData;
}

const StandardCalculatorWizard: React.FC<Props> = ({ selectedCouncil, onExit }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const totalInputSteps = 4; 
  const [calculatorData, setCalculatorData] = useState<CalculatorData>({});
  const [finalResult, setFinalResult] = useState<WindZoneResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  
  // Animation ref - Only used for input steps now
  const fadeAnim = useRef(new Animated.Value(1)).current;

  // --- HELPER FUNCTIONS ---

  const transitionToStep = (nextStep: number) => {
    // 1. Fade Out
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 150,
      useNativeDriver: true,
    }).start(() => {
      // 2. Change Step
      setCurrentStep(nextStep);
      
      // 3. Fade In
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }).start();
    });
  };

  // The Final Calculation Trigger
  const runCalculation = (completeData: CalculatorData) => {
     setIsCalculating(true);
     
     // Use a robust timeout to ensure UI updates before heavy lifting
     setTimeout(() => {
         try {
           if (completeData.regionData && completeData.terrainData && completeData.topographyData && completeData.shelterData) {
             const result = calculateWindZone({
               region: completeData.regionData,
               terrain: completeData.terrainData,
               topography: completeData.topographyData,
               shelter: completeData.shelterData
             });
             
             console.log("Calculation Success:", result);
             
             // CRITICAL: Set result AND loading state together
             setFinalResult(result);
             setIsCalculating(false);
             
             // DIRECT JUMP: No animation for result screen to prevent blank glitches
             setCurrentStep(5);
             
           } else {
             setIsCalculating(false);
             Alert.alert("Error", "Missing data needed for calculation.");
           }
         } catch (error) {
           setIsCalculating(false);
           console.error("Calculation Error:", error);
           Alert.alert("Calculation Error", "Something went wrong.");
         }
     }, 500); // 500ms "thinking" time
  };

  // --- STEP "NEXT" HANDLERS ---

  const handleStep1Next = (data: RegionData) => {
    setCalculatorData(prev => ({ ...prev, regionData: data }));
    transitionToStep(2);
  };

  const handleStep2Next = (data: TerrainData) => {
    setCalculatorData(prev => ({ ...prev, terrainData: data }));
    transitionToStep(3);
  };

  const handleStep3Next = (data: TopographyData) => {
    setCalculatorData(prev => ({ ...prev, topographyData: data }));
    transitionToStep(4);
  };

  const handleStep4Next = (data: ShelterData) => {
    const completeData = { ...calculatorData, shelterData: data };
    setCalculatorData(completeData);
    runCalculation(completeData);
  };

  // --- BACK / NAVIGATION HANDLERS ---

  const handleBack = () => {
    if (currentStep > 1 && currentStep <= totalInputSteps) {
      transitionToStep(currentStep - 1);
    } else if (currentStep === 5) {
       // Reset from result
       setFinalResult(null);
       setCurrentStep(4);
    } else {
      Alert.alert("Exit Calculator?", "Your current progress will be lost.", [
        { text: "Cancel", style: "cancel" },
        { text: "Exit", style: "destructive", onPress: onExit }
      ]);
    }
  };

  const handleStartOver = () => {
     setCalculatorData({});
     setFinalResult(null);
     setCurrentStep(1);
  };

  // --- RENDER CONTENT ---
  
  if (isCalculating) {
      // Show explicit loading screen instead of blank
      return (
        <SafeAreaView style={styles.container}>
            <View style={styles.centerMsg}>
                <Text style={styles.loadingText}>Calculating Wind Zone...</Text>
            </View>
        </SafeAreaView>
      );
  }

  // Render Step 5 (Result) directly without Animation wrapper to ensure it shows
  if (currentStep === 5) {
      return (
        <SafeAreaView style={styles.container} edges={['bottom']}>
           <WizardStep5Result 
             data={calculatorData} 
             result={finalResult || 'SED Required'}
             onRestart={handleStartOver} 
             onExit={onExit} 
             onEdit={handleBack} 
           />
        </SafeAreaView>
      );
  }

  // Render Input Steps (1-4) with Animation
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Header */}
      <View style={styles.wizardHeader}>
        <View>
           <Text style={styles.councilLabel}>{selectedCouncil.name}</Text>
           <Text style={styles.headerSubtext}>NZS 3604 Calculation</Text>
        </View>
        <View style={styles.progressContainer}>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${((currentStep-1) / totalInputSteps) * 100}%` }]} />
          </View>
          <Text style={styles.stepIndicator}>Step {currentStep}/{totalInputSteps}</Text>
          <TouchableOpacity onPress={handleBack} style={styles.closeBtn} activeOpacity={0.7}>
             <Ionicons name="close" size={24} color="#A0A0A0" />
          </TouchableOpacity>
        </View>
      </View>
      
      {/* Animated Content */}
      <Animated.View 
        style={[styles.contentContainer, { opacity: fadeAnim }]}
        key={`step-${currentStep}`}
      >
        {currentStep === 1 && <WizardStep1Region onNext={handleStep1Next} onBack={handleBack} initialData={calculatorData.regionData} />}
        {currentStep === 2 && <WizardStep2Terrain onNext={handleStep2Next} onBack={handleBack} initialData={calculatorData.terrainData} />}
        {currentStep === 3 && <WizardStep3Topography onNext={handleStep3Next} onBack={handleBack} initialData={calculatorData.topographyData} />}
        {currentStep === 4 && <WizardStep4Shelter onNext={handleStep4Next} onBack={handleBack} initialData={calculatorData.shelterData} />}
      </Animated.View>
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
  loadingText: { color: '#F97316', fontSize: 18, fontWeight: 'bold' }
});

export default StandardCalculatorWizard;
