/**
 * Environment configuration for STRYDA  
 * HARDCODED to preview URL to break cache issues
 */

export const ENV = {
  API_BASE: "https://integrity-hub-5.preview.emergentagent.com",
  USE_BACKEND: true,
} as const;

console.log('🔧 Environment Config (HARDCODED PREVIEW):', ENV);