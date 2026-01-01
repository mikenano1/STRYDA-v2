import { View, Text, ScrollView, TouchableOpacity, Modal, FlatList, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Camera, Map, Calculator, Grid, ChevronDown, Clock, Search, X, Check } from "lucide-react-native";
import { useRouter, Link } from "expo-router";
import { useState, useEffect } from "react";
import { getProjects, Project } from "../../src/internal/lib/api";

export default function DashboardScreen() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    console.log("🔄 Loading projects...");
    setLoading(true);
    try {
        const data = await getProjects();
        console.log("✅ Projects loaded:", data.length);
        setProjects(data);
        if (data.length > 0) {
        setSelectedProject(data[0]);
        }
    } catch (e) {
        console.error("❌ Failed to load projects:", e);
    } finally {
        setLoading(false);
    }
  };

  const handleProjectPress = () => {
    console.log("🔘 Project selector pressed");
    setModalVisible(true);
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
            
            <TouchableOpacity 
              className="flex-row items-center mt-1"
              onPress={() => setModalVisible(true)}
            >
              <Text className="text-white text-xl font-bold mr-2">
                {selectedProject ? selectedProject.name : "Select Project"}
              </Text>
              <ChevronDown size={20} color="#FF6B00" />
            </TouchableOpacity>
          </View>
          <TouchableOpacity className="bg-neutral-800 p-3 rounded-full border border-neutral-700">
             <Search size={24} color="white" />
          </TouchableOpacity>
        </View>

        {/* Project Selection Modal */}
        <Modal
          animationType="slide"
          transparent={true}
          visible={modalVisible}
          onRequestClose={() => setModalVisible(false)}
        >
          <View className="flex-1 justify-end bg-black/50">
            <View className="bg-neutral-900 rounded-t-3xl h-[50%] border-t border-neutral-700">
              <View className="flex-row justify-between items-center p-4 border-b border-neutral-800">
                <Text className="text-white text-lg font-bold">Select Project</Text>
                <TouchableOpacity onPress={() => setModalVisible(false)} className="p-2">
                  <X size={24} color="#999" />
                </TouchableOpacity>
              </View>
              
              {loading ? (
                <ActivityIndicator color="#FF6B00" size="large" className="mt-10" />
              ) : (
                <FlatList
                  data={projects}
                  keyExtractor={(item) => item.id}
                  contentContainerStyle={{ padding: 16 }}
                  renderItem={({ item }) => (
                    <TouchableOpacity 
                      className={`p-4 mb-3 rounded-xl border ${selectedProject?.id === item.id ? 'bg-orange-900/20 border-orange-500' : 'bg-neutral-800 border-neutral-700'}`}
                      onPress={() => {
                        setSelectedProject(item);
                        setModalVisible(false);
                      }}
                    >
                      <View className="flex-row justify-between items-center">
                        <View>
                            <Text className={`font-bold text-lg ${selectedProject?.id === item.id ? 'text-orange-500' : 'text-white'}`}>{item.name}</Text>
                            {item.address && <Text className="text-neutral-400 text-sm">{item.address}</Text>}
                        </View>
                        {selectedProject?.id === item.id && <Check size={20} color="#F97316" />}
                      </View>
                    </TouchableOpacity>
                  )}
                />
              )}
            </View>
          </View>
        </Modal>

        {/* Primary Action Grid */}
        <Text className="text-white text-lg font-bold mb-4">Quick Actions</Text>
        <View className="flex-row flex-wrap justify-between gap-y-4">
          {/* Card 1: Quick Verify - Goes to Chat */}
          <Link href={{ pathname: "/(tabs)/stryda", params: { initialQuery: "I need to verify something on site. What details do you need?" }}} asChild>
            <TouchableOpacity className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between">
              <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
                <Camera size={24} color="#FF6B00" />
              </View>
              <Text className="text-white text-lg font-bold">Quick Verify</Text>
            </TouchableOpacity>
          </Link>

          {/* Card 2: Wind Zones - GOES TO VISUAL CALCULATOR (Not Chat) */}
          <Link href="/(tabs)/wind" asChild>
            <TouchableOpacity className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between">
              <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
                <Map size={24} color="#FF6B00" />
              </View>
              <Text className="text-white text-lg font-bold">Wind Zones</Text>
            </TouchableOpacity>
          </Link>

          {/* Card 3: Bracing Calc - Goes to Chat */}
          <Link href={{ pathname: "/(tabs)/stryda", params: { initialQuery: "I need to calculate bracing. What details do you need?" }}} asChild>
            <TouchableOpacity className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between">
              <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
                <Calculator size={24} color="#FF6B00" />
              </View>
              <Text className="text-white text-lg font-bold">Bracing Calc</Text>
            </TouchableOpacity>
          </Link>

          {/* Card 4: Flashings Matrix - Goes to Chat */}
          <Link href={{ pathname: "/(tabs)/stryda", params: { initialQuery: "Show me the E2/AS1 selection tables (Table 7) for flashings" }}} asChild>
            <TouchableOpacity className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between">
              <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
                <Grid size={24} color="#FF6B00" />
              </View>
              <Text className="text-white text-lg font-bold">Flashings</Text>
            </TouchableOpacity>
          </Link>
        </View>

        {/* Recent History */}
        <Text className="text-white text-lg font-bold mt-8 mb-4">Recent Questions</Text>
        <View className="gap-3 mb-10">
          {recentHistory.map((item, index) => (
            <Link key={index} href={{ pathname: "/(tabs)/stryda", params: { initialQuery: item }}} asChild>
              <TouchableOpacity className="flex-row items-center bg-neutral-800 p-4 rounded-xl border border-neutral-700">
                <Clock size={20} color="#777" className="mr-3" />
                <Text className="text-neutral-300 font-medium flex-1">{item}</Text>
                <ChevronDown size={20} color="#555" style={{ transform: [{ rotate: '-90deg' }] }} />
              </TouchableOpacity>
            </Link>
          ))}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}
