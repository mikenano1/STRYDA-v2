import { View, Text, ScrollView, TouchableOpacity } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Camera, Map, Calculator, Grid, ChevronDown, Clock, Search } from "lucide-react-native";
import { useRouter } from "expo-router";

export default function DashboardScreen() {
  const router = useRouter();

  const handleQuickAction = (query: string) => {
    // Navigate to the tab first
    router.push('/(tabs)/stryda');
    // Use a short timeout to ensure the component is mounted before setting params
    setTimeout(() => {
      router.setParams({ initialQuery: query });
    }, 100);
  };

  const recentHistory = [
    "E2/AS1 Sill Flashing requirements",
    "NZS 3604 Bracing calculations",
    "H1 insulation schedule method"
  ];

  return (
    <SafeAreaView className="flex-1 bg-stryda-dark">
      <ScrollView className="flex-1 p-6">
        
        {/* Header */}
        <View className="flex-row justify-between items-center mb-8">
          <View>
            <Text className="text-neutral-400 text-sm font-medium">Kia Ora, Builder</Text>
            <TouchableOpacity className="flex-row items-center mt-1">
              <Text className="text-white text-xl font-bold mr-2">123 Queen St</Text>
              <ChevronDown size={20} color="#FF6B00" />
            </TouchableOpacity>
          </View>
          <TouchableOpacity className="bg-neutral-800 p-3 rounded-full border border-neutral-700">
             <Search size={24} color="white" />
          </TouchableOpacity>
        </View>

        {/* Primary Action Grid */}
        <Text className="text-white text-lg font-bold mb-4">Quick Actions</Text>
        <View className="flex-row flex-wrap justify-between gap-y-4">
          {/* Card 1: Quick Verify */}
          <TouchableOpacity 
            className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between"
            onPress={() => handleQuickAction("I need to verify something on site. What details do you need?")}
          >
            <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
              <Camera size={24} color="#FF6B00" />
            </View>
            <Text className="text-white text-lg font-bold">Quick Verify</Text>
          </TouchableOpacity>

          {/* Card 2: Wind Zones */}
          <TouchableOpacity 
            className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between"
            onPress={() => handleQuickAction("Help me find the wind zone for a site address.")}
          >
            <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
              <Map size={24} color="#FF6B00" />
            </View>
            <Text className="text-white text-lg font-bold">Wind Zones</Text>
          </TouchableOpacity>

          {/* Card 3: Bracing Calc */}
          <TouchableOpacity 
            className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between"
            onPress={() => handleQuickAction("I need to calculate bracing. What details do you need?")}
          >
            <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
              <Calculator size={24} color="#FF6B00" />
            </View>
            <Text className="text-white text-lg font-bold">Bracing Calc</Text>
          </TouchableOpacity>

          {/* Card 4: Flashings Matrix */}
          <TouchableOpacity 
            className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between"
            onPress={() => handleQuickAction("Show me the E2/AS1 Flashing Matrix for cladding junctions.")}
          >
            <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
              <Grid size={24} color="#FF6B00" />
            </View>
            <Text className="text-white text-lg font-bold">Flashings</Text>
          </TouchableOpacity>
        </View>

        {/* Recent History */}
        <Text className="text-white text-lg font-bold mt-8 mb-4">Recent Questions</Text>
        <View className="gap-3 mb-10">
          {recentHistory.map((item, index) => (
            <TouchableOpacity 
              key={index} 
              className="flex-row items-center bg-neutral-800 p-4 rounded-xl border border-neutral-700"
              onPress={() => handleQuickAction(item)}
            >
              <Clock size={20} color="#777" className="mr-3" />
              <Text className="text-neutral-300 font-medium flex-1">{item}</Text>
              <ChevronDown size={20} color="#555" style={{ transform: [{ rotate: '-90deg' }] }} />
            </TouchableOpacity>
          ))}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}
