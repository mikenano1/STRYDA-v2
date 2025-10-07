/**
 * Environment configuration for STRYDA  
 * ALWAYS defaults to preview URL - no localhost fallbacks
 */

export const ENV = {
  API_BASE: process.env.EXPO_PUBLIC_API_BASE ?? "https://onsite-copilot.preview.emergentagent.com",
  USE_BACKEND: process.env.EXPO_PUBLIC_USE_BACKEND === "true",
} as const;

console.log('🔧 Environment Config (PREVIEW LOCKED):', ENV);