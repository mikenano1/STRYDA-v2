import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const theme = {
  bg: '#111111',
  accent: '#FF7A00',
  text: '#FFFFFF'
};

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: theme.accent,
        tabBarInactiveTintColor: '#777777',
        tabBarStyle: {
          backgroundColor: '#000000',
          borderTopColor: '#333333',
          height: 85,
          paddingBottom: 25,
          paddingTop: 8,
        },
        headerShown: false,
      }}>
      {/* EXACTLY 4 TABS - HARDCODED */}
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: 'Chat',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="chatbubble-ellipses" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="library"
        options={{
          title: 'Library',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="library" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="work"
        options={{
          title: 'Tools',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="construct" size={size} color={color} />
          ),
        }}
      />
      
      {/* HIDE ALL OTHER ROUTES FROM TABS */}
      <Tabs.Screen name="index_fixed" options={{ href: null }} />
      <Tabs.Screen name="_sitemap" options={{ href: null }} />
      <Tabs.Screen name="(tabs)/ChatScreen" options={{ href: null }} />
      <Tabs.Screen name="components/ChatMessage" options={{ href: null }} />
      <Tabs.Screen name="components/CitationPill" options={{ href: null }} />
      <Tabs.Screen name="lib/telemetry" options={{ href: null }} />
      <Tabs.Screen name="state/chatStore" options={{ href: null }} />
      <Tabs.Screen name="config/constants" options={{ href: null }} />
      <Tabs.Screen name="config/env" options={{ href: null }} />
      <Tabs.Screen name="lib/api" options={{ href: null }} />
      <Tabs.Screen name="lib/api/chat" options={{ href: null }} />
      <Tabs.Screen name="lib/session" options={{ href: null }} />
      <Tabs.Screen name="state/chat" options={{ href: null }} />
      <Tabs.Screen name="types/chat" options={{ href: null }} />
    </Tabs>
  );
}