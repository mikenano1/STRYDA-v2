// app/frontend/components/wind-calculator/steps/WizardStep5Result.tsx

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { WindZone } from '../../src/internal/utils/WindZoneEngine';

interface Props {
  result: WindZone;
  onRestart: () => void;
  onExit: () => void;
}

const WizardStep5Result: React.FC<Props> = ({ result, onRestart, onExit }) => {
  
  const getResultColor = (zone: WindZone) => {
    switch (zone) {
      case 'Low': return '#10B981'; // Green
      case 'Medium': return '#3B82F6'; // Blue
      case 'High': return '#F97316'; // Orange
      case 'Very High': return '#EF4444'; // Red
      case 'SED': return '#DC2626'; // Dark Red
      default: return '#A0A0A0';
    }
  };

  const color = getResultColor(result);
  const isSED = result === 'SED';

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        
        <View style={styles.resultHeader}>
          <Text style={styles.headerLabel}>CALCULATED WIND ZONE</Text>
          <View style={[styles.zoneBadge, { borderColor: color }]}>
            <Text style={[styles.zoneText, { color: color }]}>{result}</Text>
          </View>
        </View>

        <View style={styles.divider} />

        <View style={styles.detailsContainer}>
          <Text style={styles.detailsTitle}>What this means:</Text>
          
          {isSED ? (
            <View style={styles.warningBox}>
              <Ionicons name="alert-circle" size={24} color="#DC2626" />
              <Text style={styles.warningText}>
                Specific Engineering Design (SED) is likely required. The site conditions exceed the standard limits of NZS 3604.
              </Text>
            </View>
          ) : (
            <Text style={styles.detailsText}>
              This site falls within the <Text style={{fontWeight:'bold', color}}>{result}</Text> wind zone category according to NZS 3604:2011 Section 5.
            </Text>
          )}

          <Text style={styles.referenceText}>Reference: NZS 3604:2011 Table 5.4</Text>
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

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0A0A' },
  scrollContent: { padding: 30, alignItems: 'center' },
  headerLabel: { color: '#A0A0A0', fontSize: 14, letterSpacing: 1.5, marginBottom: 20 },
  zoneBadge: {
    borderWidth: 4,
    borderRadius: 20,
    paddingVertical: 20,
    paddingHorizontal: 40,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#111',
    width: '100%',
  },
  zoneText: { fontSize: 42, fontWeight: '900', letterSpacing: 1 },
  divider: { height: 1, backgroundColor: '#222', width: '100%', marginVertical: 30 },
  detailsContainer: { width: '100%' },
  detailsTitle: { color: 'white', fontSize: 18, fontWeight: 'bold', marginBottom: 10 },
  detailsText: { color: '#D4D4D4', fontSize: 16, lineHeight: 24 },
  warningBox: { backgroundColor: 'rgba(220, 38, 38, 0.1)', padding: 15, borderRadius: 12, flexDirection: 'row', alignItems: 'center' },
  warningText: { color: '#EF4444', marginLeft: 10, flex: 1, fontSize: 15, lineHeight: 20 },
  referenceText: { color: '#555', marginTop: 20, fontSize: 12, fontStyle: 'italic' },
  footer: { flexDirection: 'row', padding: 20, borderTopWidth: 1, borderTopColor: '#222', backgroundColor: '#0A0A0A' },
  restartButton: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 15 },
  restartText: { color: '#A0A0A0', marginLeft: 8, fontWeight: '600' },
  exitButton: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#F97316', borderRadius: 8, padding: 15 },
  exitText: { color: 'white', fontWeight: 'bold', fontSize: 16 },
});

export default WizardStep5Result;
