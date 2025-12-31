// app/frontend/app/(tabs)/wind.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack } from 'expo-router';
import Step1CouncilSelect from '../../components/wind-calculator/Step1CouncilSelect';
import StandardCalculatorWizard from '../../components/wind-calculator/StandardCalculatorWizard'; // Import the new Wizard
import { Council } from '../../constants/CouncilData';
import { Ionicons } from '@expo/vector-icons';

export default function WindZoneTab() {
  const [selectedCouncil, setSelectedCouncil] = useState<Council | null>(null);

  const handleCouncilSelect = (council: Council) => {
    setSelectedCouncil(council);
  };

  const handleReset = () => {
    setSelectedCouncil(null);
  };

  // Function to open external council maps
  const openOverrideMap = () => {
    if (selectedCouncil?.mapUrl) {
      Linking.openURL(selectedCouncil.mapUrl);
    }
  };

  // RENDER STATE: Council Selected
  if (selectedCouncil) {
    const isOverride = selectedCouncil.type === 'override';

    if (isOverride) {
      // --- PATH B: OVERRIDE SCREEN ---
      // (Keeping this temporary UI for now, will beautify later)
      return (
        <SafeAreaView style={styles.container}>
          <Stack.Screen options={{ headerShown: false }} />
          <View style={styles.resultContainer}>
            <Ionicons name="alert-circle" size={80} color="#DC2626" style={{marginBottom: 20}}/>
            <Text style={styles.resultTitle}>Mandatory Map Required</Text>
            <Text style={styles.councilName}>{selectedCouncil.name}</Text>
            <Text style={styles.nextStepText}>
              This council has specific wind zone maps that override manual calculations. You must use their viewer.
            </Text>
            
            <TouchableOpacity style={[styles.actionButton, styles.overrideButton]} onPress={openOverrideMap}>
              <Text style={styles.actionButtonText}>Open Council Map Viewer</Text>
              <Ionicons name="open-outline" size={20} color="white" style={{marginLeft: 8}}/>
            </TouchableOpacity>

            <TouchableOpacity style={styles.resetButton} onPress={handleReset}>
              <Text style={styles.resetButtonText}>Back to Selection</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      );
    } else {
      // --- PATH A: STANDARD CALCULATOR WIZARD ---
      // Inject the new Wizard component here
      return (
         <>
           <Stack.Screen options={{ headerShown: false }} />
           <StandardCalculatorWizard 
              selectedCouncil={selectedCouncil} 
              onExit={handleReset} 
           />
         </>
      );
    }
  }

  // RENDER STATE 1: Show the Selection List (Default)
  return (
    <>
      <Stack.Screen options={{ headerShown: false }} />
      <Step1CouncilSelect onCouncilSelect={handleCouncilSelect} />
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  resultContainer: { 
    flex: 1, 
    justifyContent: 'center', 
    alignItems: 'center', 
    padding: 30 
  },
  resultTitle: { color: '#DC2626', fontSize: 22, fontWeight:'bold', marginBottom: 10 },
  councilName: { color: 'white', fontSize: 20, marginBottom: 25 },
  nextStepText: { color: '#A0A0A0', fontSize: 16, textAlign: 'center', marginBottom: 40 },
  actionButton: {
    flexDirection: 'row',
    paddingVertical: 16,
    paddingHorizontal: 30,
    borderRadius: 8,
    marginBottom: 20,
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  overrideButton: { backgroundColor: '#DC2626' },
  actionButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  resetButton: { padding: 15 },
  resetButtonText: { color: '#A0A0A0', fontSize: 16 }
});
