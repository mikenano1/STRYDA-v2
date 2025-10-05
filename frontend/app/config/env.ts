/**
 * Environment configuration for STRYDA
 * Typed access to environment variables
 */

export const ENV = {
  API_BASE: process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8001",
  USE_BACKEND: process.env.EXPO_PUBLIC_USE_BACKEND === "true",
} as const;

console.log('🔧 Environment Config:', ENV);