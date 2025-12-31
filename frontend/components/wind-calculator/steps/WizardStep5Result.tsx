// app/frontend/components/wind-calculator/steps/WizardStep5Result.tsx

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { CalculatorData } from '../StandardCalculatorWizard';
import { calculateWindZone, WindZoneResult } from '../../../src/internal/utils/WindZoneEngine';

interface Props {
  data: CalculatorData; // Full data collected from previous steps
  onExit: () => void;   // Exit wizard (Done)
  onRestart: () => void; // Restart calculation
}

const WizardStep5Result: React.FC<Props> = ({ data, onExit, onRestart }) => {
  const [calculating, setCalculating] = useState(true);
  const [result, setResult] = useState<WindZoneResult | null>(null);

  useEffect(() => {
    // Run calculation engine
    // Add small delay for UX "thinking" effect
    setTimeout(() => {
      if (data.regionData && data.terrainData && data.topographyData && data.shelterData) {
         const finalZone = calculateWindZone({
           region: data.regionData,
           terrain: data.terrainData,
           topography: data.topographyData,
           shelter: data.shelterData
         });
         setResult(finalZone);
      } else {
         setResult('SED Required'); // Fallback if data missing
      }
      setCalculating(false);
    }, 800);
  }, []);


  const getResultStyle = (zone: WindZoneResult) => {
    switch (zone) {
      case 'Low': return { color: '#22c55e', icon: 'shield-check', bg: 'rgba(34, 197, 94, 0.1)' };
      case 'Medium': return { color: '#eab308', icon: 'shield', bg: 'rgba(234, 179, 8, 0.1)' };
      case 'High': return { color: '#F97316', icon: 'alert', bg: 'rgba(249, 115, 22, 0.1)' };
      case 'Very High': return { color: '#ef4444', icon: 'alert-octagon', bg: 'rgba(239, 68, 68, 0.1)' };
      case 'Extra High': return { color: '#dc2626', icon: 'flash-alert', bg: 'rgba(220, 38, 38, 0.1)' };
      default: return { color: '#DC2626', icon: 'help-circle', bg: 'rgba(220, 38, 38, 0.1)' }; // SED
    }
  };

  if (calculating) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#F97316" />
        <Text style={styles.loadingText}>Calculating Wind Zone...</Text>
      </View>
    );
  }

  const isSED = result === 'SED Required';
  const styleMeta = getResultStyle(result || 'SED Required');

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.headerTitle}>Calculation Result</Text>
        
        {/* MAIN RESULT CARD */}
        <View style={[styles.resultCard, { backgroundColor: styleMeta.bg, borderColor: styleMeta.color }]}>
           <MaterialCommunityIcons name={styleMeta.icon as any} size={60} color={styleMeta.color} style={{marginBottom: 15}} />
           <Text style={styles.resultLabel}>Calculated Wind Zone:</Text>
           <Text style={[styles.resultValue, { color: styleMeta.color }]}>{result?.toUpperCase()}</Text>
           
           {isSED && (
             <Text style={styles.sedSubtext}>
               Site conditions exceed standard NZS 3604 limits (e.g. Steep slope or Lee Zone). Specific Engineering Design is required.
             </Text>
           )}
        </View>

        {/* SUMMARY OF INPUTS */}
        {!isSED && (
          <View style={styles.summaryContainer}>
            <Text style={styles.summaryHeader}>Based on Site Inputs:</Text>
            <SummaryRow label="Region" value={`Region ${data.regionData?.region} ${data.regionData?.isLeeZone === 'yes' ? '(Lee Zone)' : ''}`} />
            <SummaryRow label="Terrain" value={capitalize(data.terrainData?.roughness)} />
            <SummaryRow label="Topography" value={capitalize(data.topographyData?.type)} />
            <SummaryRow label="Shelter" value={capitalize(data.shelterData?.shelterType)} />
          </View>
        )}

        <View style={styles.disclaimerBox}>
          <Ionicons name="information-circle" size={20} color="#A0A0A0" style={{marginRight: 8}}/>
          <Text style={styles.disclaimerText}>This is an indicative calculation based on NZS 3604 Method 2. Always verify with the local building consent authority before commencing work.</Text>
        </View>

      </ScrollView>

      {/* FOOTER ACTIONS */}
       <View style={styles.footer}>
        <TouchableOpacity style={styles.restartButton} onPress={onRestart}>
          <Ionicons name="refresh" size={20} color="#A0A0A0" />
          <Text style={styles.restartText}>Start Over</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.exitButton} onPress={onExit}>
          <Text style={styles.exitText}>Done</Text>
          <Ionicons name="checkmark" size={20} color="white" style={{marginLeft: 8}}/>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// Helper components/functions
const SummaryRow = ({label, value}: {label:string, value?:string}) => (
  <View style={styles.summaryRow}>
    <Text style={styles.summaryLabel}>{label}:</Text>
    <Text style={styles.summaryValue}>{value || '-'}</Text>
  </View>
);
const capitalize = (s?: string | null) => s ? s.charAt(0).toUpperCase() + s.slice(1) : '-';


const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0A0A0A' },
  loadingText: { color: 'white', marginTop: 20, fontSize: 16 },
  scrollContent: { padding: 20, paddingBottom: 30, alignItems: 'center' },
  headerTitle: { color: 'white', fontSize: 22, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  resultCard: {
    alignItems: 'center',
    padding: 30,
    borderRadius: 20,
    borderWidth: 3,
    marginBottom: 30,
    width: '100%',
  },
  resultLabel: { color: 'white', fontSize: 16, opacity: 0.8, marginBottom: 5 },
  resultValue: { fontSize: 32, fontWeight: '900', letterSpacing: 1, textAlign: 'center' },
  sedSubtext: { color: '#dc2626', marginTop: 15, textAlign: 'center', fontWeight: '600', fontSize: 14, lineHeight: 20 },
  summaryContainer: { backgroundColor: '#171717', padding: 20, borderRadius: 12, marginBottom: 20, width: '100%' },
  summaryHeader: { color: 'white', fontWeight: 'bold', marginBottom: 15 },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  summaryLabel: { color: '#A0A0A0' },
  summaryValue: { color: 'white', fontWeight: '600' },
  disclaimerBox: { flexDirection: 'row', backgroundColor: '#1F1F1F', padding: 15, borderRadius: 8, alignItems: 'center', width: '100%' },
  disclaimerText: { color: '#777', fontSize: 12, flex: 1, fontStyle: 'italic', lineHeight: 16 },
  footer: { flexDirection: 'row', padding: 20, borderTopWidth: 1, borderTopColor: '#222', backgroundColor: '#0A0A0A' },
  restartButton: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 15 },
  restartText: { color: '#A0A0A0', marginLeft: 8, fontWeight: '600', fontSize: 16 },
  exitButton: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#F97316', borderRadius: 12, padding: 15 },
  exitText: { color: 'white', fontWeight: 'bold', fontSize: 16 },
});

export default WizardStep5Result;
