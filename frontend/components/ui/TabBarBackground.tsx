import { BlurView } from 'expo-blur';
import { StyleSheet } from 'react-native';

export default function TabBarBackground() {
  return <BlurView tint="dark" intensity={95} style={StyleSheet.absoluteFill} />;
}