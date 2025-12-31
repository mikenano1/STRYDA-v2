// app/frontend/utils/windCalculationEngine.ts

import { RegionData } from '../components/wind-calculator/steps/WizardStep1Region';
import { TerrainData } from '../components/wind-calculator/steps/WizardStep2Terrain';
import { TopographyData } from '../components/wind-calculator/steps/WizardStep3Topography';
import { ShelterData } from '../components/wind-calculator/steps/WizardStep4Shelter';

export type WindZoneResult = 'Low' | 'Medium' | 'High' | 'Very High' | 'Extra High' | 'SED Required';

interface CalculationInputs {
  region: RegionData;
  terrain: TerrainData;
  topography: TopographyData;
  shelter: ShelterData;
}

/**
 * THE BRAIN: Implements NZS 3604:2011 Section 5, Method 2.
 * This is a simplified implementation for the Alpha prototype based on standard table logic.
 */
export function calculateWindZone(inputs: CalculationInputs): WindZoneResult {
  const { region, terrain, topography, shelter } = inputs;

  // 1. IMMEDIATE SED TRIGGERS (The "Exit Ramps")
  if (topography.type === 'steep') {
    return 'SED Required'; // NZS 3604 5.2.3 - Steep slopes usually require specific design or exceed limits
  }
  // Note: Lee Zone 'yes' is a strong indicator for SED, but sometimes allows calculation with penalties. 
  // For Alpha safety, we'll push heavy Lee Zones towards SED or Extra High.

  let score = 0;

  // 2. BASELINE SCORE FROM TERRAIN & SHELTER (Simplified Table Logic)
  // Urban + Sheltered is the best case (lowest wind)
  if (terrain.roughness === 'urban') {
    score += (shelter.shelterType === 'sheltered') ? 1 : 2;
  } else if (terrain.roughness === 'open') {
    score += (shelter.shelterType === 'sheltered') ? 2 : 3;
  } else if (terrain.roughness === 'coastal') {
     // Coastal is naturally higher
    score += (shelter.shelterType === 'sheltered') ? 3 : 4;
  }

  // 3. TOPOGRAPHY MULTIPLIER (Speed-up over hills)
  if (topography.type === 'hill') {
    score += 1; // Moderate hill penalty
  } 
  // Steep topography handled in immediate triggers

  // 4. REGION & LEE ZONE ADJUSTMENTS
  // Region W bumps everything up a notch
  if (region.region === 'W') {
    score += 1;
  }
  // Lee Zones impose significant penalties
  if (region.isLeeZone === 'yes') {
      score += 2; 
  }


  // 5. FINAL DETERMINATION MAPPING based on accumulated score
  // Scores are arbitrary buckets representing relative wind speed tiers.
  if (score <= 1) return 'Low';
  if (score === 2) return 'Medium';
  if (score === 3) return 'High';
  if (score === 4) return 'Very High';
  if (score === 5) return 'Extra High';
  
  // Anything higher is off the charts
  return 'SED Required';
}
