/**
 * STRYDA Configuration Constants
 * Single source of truth for API configuration
 */

// CRITICAL: Always use preview URL as default, no localhost fallbacks
export const API_CONFIG = {
  // Use preview URL as primary, only fallback if explicitly set to localhost
  BASE_URL: process.env.EXPO_PUBLIC_API_BASE || 'https://onsite-copilot.preview.emergentagent.com',
  USE_BACKEND: process.env.EXPO_PUBLIC_USE_BACKEND === 'true',
  DEBUG: process.env.CHAT_DEBUG === 'true',
} as const;

// Health check configuration
export const HEALTH_CONFIG = {
  CHECK_INTERVAL_MS: 30000, // 30 seconds
  TIMEOUT_MS: 10000, // 10 seconds
} as const;

// Chat configuration
export const CHAT_CONFIG = {
  MAX_MESSAGE_LENGTH: 1000,
  MAX_TURNS_STORED: 50,
  SESSION_KEY: 'stryda.chat.session',
} as const;

console.log('🔧 STRYDA Config Loaded:', {
  API_BASE: API_CONFIG.BASE_URL,
  USE_BACKEND: API_CONFIG.USE_BACKEND,
  DEBUG: API_CONFIG.DEBUG
});