// app/frontend/components/wind-calculator/StandardCalculatorWizard.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Council } from '../../constants/CouncilData';
import WizardStep1Region, { RegionData } from './steps/WizardStep1Region';

interface Props {
  selectedCouncil: Council;
  onExit: () => void; // Function to go back to council selection
}

// Define the interface for all collected data
export interface CalculatorData {
  regionData?: RegionData;
  // Add future steps here:
  // terrainData?: TerrainData;
  // topographyData?: TopographyData;
}

const StandardCalculatorWizard: React.FC<Props> = ({ selectedCouncil, onExit }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [calculatorData, setCalculatorData] = useState<CalculatorData>({});

  // --- STEP HANDLERS ---

  // Handle completion of Step 1 (Region/Lee Zone)
  const handleStep1Next = (data: RegionData) => {
    console.log('Step 1 Data Collected:', data);
    setCalculatorData(prev => ({ ...prev, regionData: data }));
    // Move to next step (Future implementation)
    // setCurrentStep(2); 
    alert("Step 1 Complete! Data saved. (Next steps coming soon)");
  };

  // --- RENDER CURRENT STEP ---
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <WizardStep1Region onNext={handleStep1Next} onBack={onExit} />;
      // case 2: return <WizardStep2Terrain ... />
      // case 3: return <WizardStep3Topography ... />
      default:
        return <Text style={{color: 'white'}}>Unknown Step</Text>;
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
       {/* Simple Header Showing Progress */}
      <View style={styles.wizardHeader}>
        <TouchableOpacity onPress={onExit} style={styles.closeBtn}>
           <Text style={styles.closeText}>Exit</Text>
        </TouchableOpacity>
        <Text style={styles.councilLabel}>Council: {selectedCouncil.name}</Text>
        <Text style={styles.stepIndicator}>Step {currentStep} of 5</Text>
      </View>
      
      <View style={styles.contentContainer}>
        {renderStep()}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  wizardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 15, borderBottomWidth: 1, borderBottomColor: '#222' },
  closeBtn: { padding: 8 },
  closeText: { color: '#A0A0A0' },
  councilLabel: { color: 'white', fontWeight: '600' },
  stepIndicator: { color: '#F97316', fontWeight: 'bold' },
  contentContainer: { flex: 1 },
});

export default StandardCalculatorWizard;
