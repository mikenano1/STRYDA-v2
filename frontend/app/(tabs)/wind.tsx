// app/frontend/app/(tabs)/wind.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack } from 'expo-router';
import Step1CouncilSelect from '../../components/wind-calculator/Step1CouncilSelect';
import { Council } from '../../constants/CouncilData';
import { Ionicons } from '@expo/vector-icons';

export default function WindZoneTab() {
  // State to manage which council has been selected
  const [selectedCouncil, setSelectedCouncil] = useState<Council | null>(null);

  // Handler for when a user taps a council in the list
  const handleCouncilSelect = (council: Council) => {
    console.log('Attempting to select council:', council.name);
    // In the future, this will trigger navigation to the next step.
    // For now, it updates state to show the temporary confirmation screen.
    setSelectedCouncil(council);
  };

  // Handler to reset selection and go back to the list
  const handleReset = () => {
    setSelectedCouncil(null);
  };

  // RENDER STATE 2: Council Selected (Temporary Placeholder)
  if (selectedCouncil) {
    const isOverride = selectedCouncil.type === 'override';
    return (
      <SafeAreaView style={styles.container}>
        <Stack.Screen options={{ headerShown: false }} />
        <View style={styles.resultContainer}>
          <Ionicons 
            name={isOverride ? "alert-circle" : "checkmark-circle"} 
            size={80} 
            color={isOverride ? "#DC2626" : "#F97316"} 
            style={{marginBottom: 20}}
          />
          <Text style={styles.resultTitle}>Selection Confirmed</Text>
          <Text style={styles.councilName}>{selectedCouncil.name}</Text>
          
          <View style={[styles.typeBadge, isOverride ? styles.badgeOverride : styles.badgeStandard]}>
             <Text style={styles.typeText}>
               TYPE: {isOverride ? 'OVERRIDE MAP REQUIRED' : 'STANDARD CALCULATION'}
             </Text>
          </View>

          <Text style={styles.nextStepText}>
            {isOverride 
              ? "Next Step: Redirect to Council Map Viewer." 
              : "Next Step: Begin NZS 3604 Calculator Wizard."}
          </Text>

          <TouchableOpacity style={styles.resetButton} onPress={handleReset}>
            <Text style={styles.resetButtonText}>Change Selection</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
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
  resultTitle: { color: '#A0A0A0', fontSize: 18, marginBottom: 10 },
  councilName: { color: 'white', fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginBottom: 25 },
  typeBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 40,
  },
  badgeStandard: { backgroundColor: 'rgba(249, 115, 22, 0.2)' },
  badgeOverride: { backgroundColor: 'rgba(220, 38, 38, 0.2)' },
  typeText: { color: 'white', fontWeight: '700', letterSpacing: 1 },
  nextStepText: { color: 'gray', fontSize: 16, textAlign: 'center', marginBottom: 50 },
  resetButton: {
    paddingVertical: 12,
    paddingHorizontal: 30,
    backgroundColor: '#1F1F1F',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333'
  },
  resetButtonText: { color: 'white', fontSize: 16, fontWeight: '600' }
});
