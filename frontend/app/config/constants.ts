/**
 * STRYDA Configuration Constants
 * SINGLE SOURCE OF TRUTH - Preview URL only, no localhost fallbacks
 */

export const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? 'https://onsite-copilot.preview.emergentagent.com';

export const CONFIG = {
  API_BASE,
  USE_BACKEND: process.env.EXPO_PUBLIC_USE_BACKEND === 'true',
  DEBUG: process.env.CHAT_DEBUG === 'true',
} as const;

// Log once at startup
console.log('[config] API_BASE=' + API_BASE);