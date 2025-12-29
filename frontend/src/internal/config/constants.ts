/**
 * STRYDA Configuration Constants
 * Hardcoded preview URL for production deployment
 */

export const API_BASE = "https://nzconstructai.preview.emergentagent.com";
export const FEATURE_TIER1 = true;

export const CONFIG = {
  API_BASE,
  USE_BACKEND: true,
  DEBUG: process.env.CHAT_DEBUG === 'true',
  FEATURE_TIER1,
} as const;

// Log configuration for debugging
console.log('[config] STRYDA Production Config:', {
  API_BASE,
  FEATURE_TIER1
});