import { Tabs } from 'expo-router';

export default function Layout() {
  return (
    <Tabs screenOptions={{ headerShown: false }}>
      {/* ONLY 4 TABS - EVERYTHING ELSE HIDDEN */}
      <Tabs.Screen name="index"   options={{ title: 'Home'    }} />
      <Tabs.Screen name="chat"    options={{ title: 'Chat'    }} />
      <Tabs.Screen name="library" options={{ title: 'Library' }} />
      <Tabs.Screen name="work"    options={{ title: 'Tools'   }} />
      
      {/* HIDE ALL OTHER DISCOVERED ROUTES */}
      <Tabs.Screen name="_sitemap" options={{ href: null }} />
      <Tabs.Screen name="+not-found" options={{ href: null }} />
      <Tabs.Screen name="(tabs)/ChatScreen" options={{ href: null }} />
      <Tabs.Screen name="internal/DiagOverlay" options={{ href: null }} />
      <Tabs.Screen name="internal/chat" options={{ href: null }} />
      <Tabs.Screen name="internal/index_fixed" options={{ href: null }} />
      <Tabs.Screen name="internal/library" options={{ href: null }} />
      <Tabs.Screen name="internal/work" options={{ href: null }} />
      <Tabs.Screen name="internal/components/ChatMessage" options={{ href: null }} />
      <Tabs.Screen name="internal/components/CitationPill" options={{ href: null }} />
      <Tabs.Screen name="internal/lib/telemetry" options={{ href: null }} />
      <Tabs.Screen name="internal/state/chatStore" options={{ href: null }} />
      <Tabs.Screen name="internal/config/constants" options={{ href: null }} />
      <Tabs.Screen name="internal/config/env" options={{ href: null }} />
      <Tabs.Screen name="internal/lib/api" options={{ href: null }} />
      <Tabs.Screen name="internal/lib/session" options={{ href: null }} />
      <Tabs.Screen name="internal/state/chat" options={{ href: null }} />
      <Tabs.Screen name="internal/types/chat" options={{ href: null }} />
      <Tabs.Screen name="internal/diag" options={{ href: null }} />
    </Tabs>
  );
}