// This file is a fallback for using SF Symbols on iOS and Android
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { SymbolWeight, SymbolScale } from 'expo-symbols';
import { StyleProp, ViewStyle, TextStyle } from 'react-native';

// Add type import for SF Symbols
const MAPPING = {
  // Home tab
  'house.fill': 'home',
  // Work tab  
  'briefcase.fill': 'work',
  // Library tab
  'books.vertical.fill': 'library-books',
  // Chat/messaging
  'message.fill': 'message',
  'paperplane.fill': 'send',
  // Voice/audio
  'mic.fill': 'mic',
  'waveform': 'graphic-eq',
  // Settings/more
  'gearshape.fill': 'settings',
  'ellipsis': 'more-horiz',
  // Navigation
  'chevron.left': 'chevron-left',
  'chevron.right': 'chevron-right',
  'plus': 'add',
  'xmark': 'close',
  // Content
  'photo': 'photo',
  'doc.text': 'description',
  'folder.fill': 'folder',
  // Status
  'checkmark.circle.fill': 'check-circle',
  'exclamationmark.triangle.fill': 'warning',
  'info.circle.fill': 'info',
} as const;

export type IconSymbolName = keyof typeof MAPPING;

interface IconSymbolProps {
  name: IconSymbolName;
  size?: number;
  color?: string;
  style?: StyleProp<ViewStyle & TextStyle>;
  weight?: SymbolWeight;
  scale?: SymbolScale;
}

export function IconSymbol({ name, size = 24, color, style, weight, scale }: IconSymbolProps) {
  return (
    <MaterialIcons
      color={color}
      size={size}
      name={MAPPING[name]}
      style={style}
    />
  );
}