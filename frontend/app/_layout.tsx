import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function RootLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#FF7A00', // STRYDA orange
        tabBarInactiveTintColor: '#777777',
        tabBarStyle: {
          backgroundColor: '#111111', // STRYDA dark background
          borderTopWidth: 1,
          borderTopColor: '#333333',
          paddingBottom: 30, // More space for labels
          paddingTop: 10,
          height: 90, // Taller to fit labels properly
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '500',
          marginTop: 4, // Space between icon and label
        },
      }}>
      {/* EXACTLY 4 TABS - MATCHING EXACT FILE NAMES */}
      <Tabs.Screen
        name="(tabs)/index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => (
            <Ionicons name="home" size={20} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="(tabs)/chat"
        options={{
          title: 'Chat',
          tabBarIcon: ({ color }) => (
            <Ionicons name="chatbubble-ellipses" size={20} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="(tabs)/library" 
        options={{
          title: 'Library',
          tabBarIcon: ({ color }) => (
            <Ionicons name="library" size={20} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="(tabs)/work"
        options={{
          title: 'Tools',
          tabBarIcon: ({ color }) => (
            <Ionicons name="construct" size={20} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}