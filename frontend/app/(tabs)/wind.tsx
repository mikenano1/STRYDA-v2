// app/frontend/app/(tabs)/wind.tsx

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Linking, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

// --- IMPORT THE NEW UI LAYOUT COMPONENTS ---
import Step1RegionSelect from '../../components/wind-calculator/Step1RegionSelect';
import Step1bCouncilSelect from '../../components/wind-calculator/Step1bCouncilSelect';

// --- IMPORT THE FINISHED CALCULATOR WIZARD ---
import StandardCalculatorWizard from '../../components/wind-calculator/StandardCalculatorWizard';
import { Council, Region } from '../../constants/CouncilData';

export default function WindZoneTab() {
  // State manages the multi-stage selection flow
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null);
  const [selectedCouncil, setSelectedCouncil] = useState<Council | null>(null);

  // --- Handlers ---

  const handleRegionSelect = (region: Region) => {
    setSelectedRegion(region);
  };

  const handleCouncilSelect = (council: Council) => {
    setSelectedCouncil(council);
  };

  // Go back one step (Council list -> Region list)
  const handleBackToRegions = () => {
    setSelectedRegion(null);
  };

  // Full reset from Calculator/Override screen back to start
  const handleReset = () => {
    setSelectedCouncil(null);
    setSelectedRegion(null);
  };

  // Function to launch external council maps (for override councils)
  const openOverrideMap = async () => {
    if (selectedCouncil?.mapUrl) {
      try {
        const supported = await Linking.canOpenURL(selectedCouncil.mapUrl);
        if (supported) {
          await Linking.openURL(selectedCouncil.mapUrl);
        } else {
          Alert.alert("Error", "Cannot open this URL format: " + selectedCouncil.mapUrl);
        }
      } catch (err) {
        console.error("Failed to open URL:", err);
        Alert.alert("Error", "Could not launch the map viewer. Check internet connection.");
      }
    } else {
      Alert.alert("Configuration Error", "No map URL found for this council.");
    }
  };


  // --- MAIN RENDER LOGIC (Cascading State) ---

  // STATE 3: Council Selected -> Decide: Wizard or Override Screen?
  if (selectedCouncil) {
    const isOverride = selectedCouncil.type === 'override';

    if (isOverride) {
      // --- PATH B: OVERRIDE SCREEN (Mandatory Map) ---
      return (
        <SafeAreaView style={styles.container}>
          <Stack.Screen options={{ headerShown: false }} />
          <View style={styles.overrideContainer}>
            <View style={styles.iconHeader}>
               <Ionicons name="map" size={50} color="#DC2626" />
               <Ionicons name="alert-circle" size={30} color="#DC2626" style={styles.alertBadge}/>
            </View>
            
            <Text style={styles.resultTitle}>Mandatory Map Required</Text>
            <Text style={styles.councilName}>{selectedCouncil.name}</Text>
            
            <View style={styles.infoBox}>
               <Text style={styles.infoBoxText}>
                  This authority has specific wind zone maps that **override** manual NZS 3604 calculations. You must use their official viewer.
               </Text>
            </View>
            
            <TouchableOpacity style={[styles.actionButton, styles.overrideButton]} onPress={openOverrideMap} activeOpacity={0.8}>
              <Text style={styles.actionButtonText}>Open Official Map Viewer</Text>
              <Ionicons name="open-outline" size={22} color="white" style={{marginLeft: 10}}/>
            </TouchableOpacity>

            <TouchableOpacity style={styles.resetButton} onPress={handleReset}>
              <Text style={styles.resetButtonText}>Back to Region Selection</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      );
    } else {
      // --- PATH A: STANDARD CALCULATOR WIZARD ---
      // Launches the finished multi-step wizard component
      return (
         <>
           <Stack.Screen options={{ headerShown: false }} />
           <StandardCalculatorWizard
              selectedCouncil={selectedCouncil}
              onExit={handleReset} // Exit now goes back to region select start
           />
         </>
      );
    }
  }

  // STATE 2: Region Selected -> Show Council List for that Region
  if (selectedRegion) {
    return (
      <>
        <Stack.Screen options={{ headerShown: false }} />
        <Step1bCouncilSelect
          region={selectedRegion}
          onCouncilSelect={handleCouncilSelect}
          onBack={handleBackToRegions}
        />
      </>
    );
  }

  // STATE 1 (Default): No Selection -> Show Region List
  return (
    <>
      <Stack.Screen options={{ headerShown: false }} />
      <Step1RegionSelect onRegionSelect={handleRegionSelect} />
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  overrideContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 30, paddingBottom: 50 },
  iconHeader: { marginBottom: 25, position: 'relative' },
  alertBadge: { position: 'absolute', top: -5, right: -5, backgroundColor: '#0A0A0A', borderRadius: 15 },
  resultTitle: { color: '#DC2626', fontSize: 24, fontWeight:'bold', marginBottom: 10, letterSpacing: 0.5 },
  councilName: { color: 'white', fontSize: 22, marginBottom: 30, fontWeight: '500' },
  infoBox: { backgroundColor: 'rgba(220, 38, 38, 0.1)', padding: 20, borderRadius: 12, marginBottom: 30, width: '100%' },
  infoBoxText: { color: '#A0A0A0', fontSize: 16, textAlign: 'center', lineHeight: 24 },
  actionButton: { flexDirection: 'row', paddingVertical: 18, paddingHorizontal: 30, borderRadius: 12, marginBottom: 20, alignItems: 'center', justifyContent: 'center', width: '100%', shadowColor: '#DC2626', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 5 },
  overrideButton: { backgroundColor: '#DC2626' },
  actionButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  resetButton: { padding: 15, marginTop: 10 },
  resetButtonText: { color: '#777', fontSize: 16, fontWeight: '600' }
});
