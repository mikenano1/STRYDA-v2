import { Tabs } from "expo-router";
import { View, Platform } from "react-native";
import { LayoutDashboard, FolderOpen, MessageSquare, BookOpen, Wind } from "lucide-react-native";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: "#121212",
          borderTopColor: "#333333",
          borderTopWidth: 1,
          height: Platform.OS === "ios" ? 85 : 60,
          paddingBottom: Platform.OS === "ios" ? 30 : 10,
          paddingTop: 10,
        },
        tabBarActiveTintColor: "#FF6B00",
        tabBarInactiveTintColor: "#777777",
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "600",
          marginTop: 4,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => <LayoutDashboard color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="projects"
        options={{
          title: "Projects",
          tabBarIcon: ({ color, size }) => <FolderOpen color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="stryda"
        options={{
          title: "STRYDA",
          tabBarLabelStyle: {
            color: '#FF6B00',
            fontWeight: 'bold',
            marginTop: 4,
          },
          tabBarIcon: ({ color, size }) => (
            <View className="bg-stryda-orange rounded-full p-3 -mt-8 shadow-lg shadow-black/50 border-4 border-[#121212]">
              <MessageSquare color="white" size={24} fill="white" />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="library"
        options={{
          title: "Library",
          tabBarIcon: ({ color, size }) => <BookOpen color={color} size={size} />,
        }}
      />
      {/* Wind tab hidden from bar but registered as a route */}
      <Tabs.Screen 
        name="wind" 
        options={{ 
          href: null,
          title: "Wind Calc"
        }} 
      />
      {/* Remove 'work' if it's unused, or keep hidden */}
      <Tabs.Screen name="work" options={{ href: null }} />
    </Tabs>
  );
}
