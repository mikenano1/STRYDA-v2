import { API_BASE } from "../config/constants";

export const config = {
  // Use centralized API_BASE - no localhost fallbacks
  API_BASE: API_BASE,
  USE_BACKEND: process.env.EXPO_PUBLIC_USE_BACKEND === 'true' || false,
};

console.log('🔧 API Config:', config);
