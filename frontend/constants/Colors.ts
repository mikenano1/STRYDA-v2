/**
 * STRYDA.ai Color Palette
 * Optimized for on-site readability with dark mode lock
 * Professional tradie-focused design
 */

const tintColorLight = '#0a84ff';
const tintColorDark = '#ff9f40'; // Construction orange accent

export const Colors = {
  light: {
    text: '#11181C',
    background: '#fff',
    tint: tintColorLight,
    icon: '#687076',
    tabIconDefault: '#687076',
    tabIconSelected: tintColorLight,
  },
  dark: {
    // Primary colors for STRYDA.ai - high contrast for on-site use
    text: '#ECEDEE',           // Pure white for maximum readability
    background: '#0c0c0c',     // Deep black background (as specified)
    surface: '#1a1a1a',       // Slightly lighter surface for cards/panels
    surfaceSecondary: '#2a2a2a', // Secondary surface for layering
    
    // Accent colors
    tint: '#ff9f40',           // Construction orange - primary CTA color
    primary: '#ff9f40',        // Primary brand color
    secondary: '#4a90e2',      // Blue for secondary actions
    success: '#34c759',        // Green for success states
    warning: '#ff9500',        // Orange for warnings
    error: '#ff3b30',          // Red for errors
    
    // Interactive elements
    icon: '#9ba1a6',           // Default icon color
    tabIconDefault: '#6c7378', // Inactive tab icons
    tabIconSelected: '#ff9f40', // Active tab icons (matches tint)
    
    // UI elements
    border: '#2a2a2a',         // Subtle borders
    inputBackground: '#1a1a1a', // Input field backgrounds
    placeholder: '#6c7378',    // Placeholder text
    
    // Chat specific colors
    messageUser: '#ff9f40',    // User message bubble
    messageBot: '#2a2a2a',     // Bot message bubble
    messageText: '#ECEDEE',    // Message text
    
    // Status colors for jobs
    statusActive: '#34c759',
    statusPending: '#ff9500',
    statusComplete: '#4a90e2',
  },
};

// Brand specific colors for STRYDA.ai
export const BrandColors = {
  // Primary brand palette
  orange: '#ff9f40',        // Primary brand color
  orangeLight: '#ffb366',   // Lighter variant for hover states
  orangeDark: '#e6901a',    // Darker variant for pressed states
  
  // NZ Building industry inspired colors
  safetyOrange: '#ff6600',  // High visibility safety color
  hardhat: '#ffcc00',       // Yellow hard hat color
  blueprint: '#0066cc',     // Blueprint blue
  
  // Surface variations for depth
  surface1: '#0c0c0c',      // Base surface (same as background)
  surface2: '#1a1a1a',      // Elevated surface 1
  surface3: '#2a2a2a',      // Elevated surface 2
  surface4: '#3a3a3a',      // Elevated surface 3
};