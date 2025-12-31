// app/frontend/src/internal/utils/WindZoneEngine.ts

import { RegionData } from '../../../components/wind-calculator/steps/WizardStep1Region';
import { TerrainData } from '../../../components/wind-calculator/steps/WizardStep2Terrain';
import { TopographyData } from '../../../components/wind-calculator/steps/WizardStep3Topography';
import { ShelterData } from '../../../components/wind-calculator/steps/WizardStep4Shelter';

export type WindZone = 'Low' | 'Medium' | 'High' | 'Very High' | 'SED';

interface CalculationInput {
  region: RegionData;
  terrain: TerrainData;
  topography: TopographyData;
  shelter: ShelterData;
}

export function calculateWindZone(input: CalculationInput): WindZone {
  const { region, terrain, topography, shelter } = input;

  // 1. REGION A LOGIC
  if (region.region === 'A') {
    // 1a. Low Wind Zone (The calmest scenario)
    if (
      terrain.roughness === 'urban' && 
      topography.type === 'flat' && 
      shelter.shelterType === 'sheltered'
    ) {
      return 'Low';
    }

    // 1b. Medium Wind Zone (Common suburban)
    if (
      terrain.roughness === 'urban' && 
      topography.type === 'flat' && 
      shelter.shelterType === 'exposed'
    ) {
      return 'Medium';
    }

    // 1c. High Wind Zone (Rural or gentle hills)
    if (
      (terrain.roughness === 'open' && topography.type === 'flat') ||
      (terrain.roughness === 'urban' && topography.type === 'hill' && shelter.shelterType === 'sheltered')
    ) {
      return 'High';
    }

    // 1d. Very High Wind Zone (Hilltops/Coastal)
    if (
      topography.type === 'hill' || 
      terrain.roughness === 'coastal'
    ) {
      return 'Very High';
    }
  }

  // 2. REGION W LOGIC (Wellington/High Wind Areas)
  if (region.region === 'W') {
    // Wellington basically starts at High
    if (topography.type === 'flat' && shelter.shelterType === 'sheltered') {
      return 'High';
    }
    // Everything else is Very High or SED
    if (topography.type === 'hill' || terrain.roughness === 'coastal') {
      return 'Very High';
    }
  }

  // 3. SAFETY NETS (SED Triggers)
  if (topography.type === 'steep') {
    return 'SED'; // Steep slopes almost always require SED
  }
  
  if (region.isLeeZone === 'yes') {
    // Note: In real life, Lee Zones require specific multipliers, often pushing to SED
    return 'SED';
  }

  // Default Fallback
  return 'Very High'; 
}
