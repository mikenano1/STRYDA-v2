import { Tabs } from 'expo-router';

export default function Layout() {
  return (
    <Tabs screenOptions={{ headerShown: false }}>
      <Tabs.Screen name="index"   options={{ title: 'Home'    }} />
      <Tabs.Screen name="chat"    options={{ title: 'Chat'    }} />
      <Tabs.Screen name="library" options={{ title: 'Library' }} />
      <Tabs.Screen name="work"    options={{ title: 'Tools'   }} />
    </Tabs>
  );
}