// app/frontend/components/wind-calculator/StandardCalculatorWizard.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView, TouchableOpacity, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Council } from '../../constants/CouncilData';
// Import Step 1 and its data interface
import WizardStep1Region, { RegionData } from './steps/WizardStep1Region';

interface Props {
  selectedCouncil: Council;
  onExit: () => void; // Function to go back to council selection screen
}

// Define the master interface for all collected data across all steps
export interface CalculatorData {
  regionData?: RegionData;
  // Future steps will add data here:
  // terrainData?: TerrainData;
  // topographyData?: TopographyData;
  // shelterData?: ShelterData;
}

const StandardCalculatorWizard: React.FC<Props> = ({ selectedCouncil, onExit }) => {
  // State to track current step number (Starts at 1)
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 5; // Total anticipated steps

  // State to hold all data collected from the steps
  const [calculatorData, setCalculatorData] = useState<CalculatorData>({});

  // --- STEP HANDLERS ---

  // Handler for Step 1 Completion
  const handleStep1Next = (data: RegionData) => {
    console.log('Step 1 Data Collected:', data);
    // Save data to master state
    setCalculatorData(prev => ({ ...prev, regionData: data }));
    
    // Advance to next step
    // For now, since Step 2 isn't built, we show a temporary alert.
    // setCurrentStep(2); 
    Alert.alert("Progress Saved", "Step 1 data collected. Step 2 (Terrain) is coming next.");
  };

  // Handler for back button within the wizard
  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    } else {
      // If on Step 1, confirm exit back to council selection
      Alert.alert(
        "Exit Calculator?",
        "Your progress will be lost.",
        [
          { text: "Cancel", style: "cancel" },
          { text: "Exit", style: "destructive", onPress: onExit }
        ]
      );
    }
  };

  // --- RENDER CURRENT STEP FUNCTION ---
  // Switches based on currentStep state
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <WizardStep1Region 
            onNext={handleStep1Next} 
            onBack={handleBack}
            initialData={calculatorData.regionData} // Pass back saved data if existing
          />
        );
      // Future steps will be added here:
      // case 2: return <WizardStep2Terrain onNext={...} onBack={...} />;
      // case 3: return <WizardStep3Topography onNext={...} onBack={...} />;
      default:
        return (
          <View style={styles.centerMsg}>
            <Text style={styles.errorText}>Step {currentStep} not yet implemented.</Text>
          </View>
        );
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
       {/* Wizard Header with Progress Info */}
      <View style={styles.wizardHeader}>
        <View>
           <Text style={styles.councilLabel}>{selectedCouncil.name}</Text>
           <Text style={styles.headerSubtext}>NZS 3604 Calculation</Text>
        </View>
        <View style={styles.progressContainer}>
          <Text style={styles.stepIndicator}>Step {currentStep} <Text style={{color:'#555'}}>/ {totalSteps}</Text></Text>
          <TouchableOpacity onPress={handleBack} style={styles.closeBtn}>
             <Ionicons name="close" size={24} color="#A0A0A0" />
          </TouchableOpacity>
        </View>
      </View>
      
      {/* Main Content Area Rendered by Step Component */}
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
  stepIndicator: { color: '#F97316', fontWeight: 'bold', marginRight: 15, fontSize: 16 },
  closeBtn: { padding: 4 },
  contentContainer: { flex: 1 },
  centerMsg: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  errorText: { color: 'red', fontSize: 18 }
});

export default StandardCalculatorWizard;
