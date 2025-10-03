import Constants from 'expo-constants';

export const config = {
  // Read from EXPO_PUBLIC_* environment variables
  API_BASE: process.env.EXPO_PUBLIC_API_BASE || 'http://localhost:8001',
  USE_BACKEND: process.env.EXPO_PUBLIC_USE_BACKEND === 'true' || false,
};

console.log('🔧 Config:', config);
