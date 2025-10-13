import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function RootLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#FF7A00',
        tabBarInactiveTintColor: '#888888', 
        tabBarStyle: {
          backgroundColor: '#111111',
          borderTopWidth: 0,
          paddingBottom: 25,
          paddingTop: 8,
          height: 85,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home-outline" size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: 'Chat',  
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="chatbubbles-outline" size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="library"
        options={{
          title: 'Library',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="library-outline" size={22} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="work"
        options={{
          title: 'Tools',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="build-outline" size={22} color={color} />
          ),
        }}
      />
      
      {/* AGGRESSIVELY HIDE EVERYTHING ELSE */}
      <Tabs.Screen name="_sitemap" options={{ href: null, title: '' }} />
      <Tabs.Screen name="+not-found" options={{ href: null, title: '' }} />
      <Tabs.Screen name="[...missing]" options={{ href: null, title: '' }} />
      <Tabs.Screen name="(tabs)" options={{ href: null, title: '' }} />
      <Tabs.Screen name="(tabs)/chat" options={{ href: null, title: '' }} />
      <Tabs.Screen name="(tabs)/index" options={{ href: null, title: '' }} />
      <Tabs.Screen name="(tabs)/library" options={{ href: null, title: '' }} />
      <Tabs.Screen name="(tabs)/work" options={{ href: null, title: '' }} />
      
    </Tabs>
  );
}