import { useColorScheme as _useColorScheme } from 'react-native';

// STRYDA.ai uses locked dark mode for consistent on-site readability
export function useColorScheme() {
  // Always return 'dark' to lock the app in dark mode
  return 'dark';
}

// For any future use where we might need the actual system color scheme
export function useSystemColorScheme() {
  return _useColorScheme();
}