import Constants from 'expo-constants';

export const config = {
  // Read from EXPO_PUBLIC_* environment variables
  API_BASE: Constants.expoConfig?.extra?.apiBase || 'http://localhost:8000',
  USE_BACKEND: Constants.expoConfig?.extra?.useBackend === 'true' || 
               Constants.expoConfig?.extra?.useBackend === true,
};

console.log('🔧 Config:', config);
