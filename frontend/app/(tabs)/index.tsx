import { View, Text, ScrollView, TouchableOpacity, Modal, FlatList, ActivityIndicator, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Camera, Map, Calculator, Grid, ChevronDown, Clock, Search, X, MessageSquare, Plus, Archive, ChevronRight } from "lucide-react-native";
import { useRouter, Link } from "expo-router";
import { useState, useEffect } from "react";
import { getThreads, Thread } from "../../src/internal/lib/api";

export default function DashboardScreen() {
  const router = useRouter();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadThreads();
  }, []);

  const loadThreads = async () => {
    console.log("🔄 Loading threads...");
    setLoading(true);
    try {
        const data = await getThreads();
        console.log("✅ Threads loaded:", data.length);
        setThreads(data);
    } catch (e) {
        console.error("❌ Failed to load threads:", e);
    } finally {
        setLoading(false);
    }
  };

  const handleNewChat = () => {
      // Navigate to chat with no session ID to start fresh
      router.push("/(tabs)/stryda");
  };

  const handleThreadSelect = (thread: Thread) => {
      setModalVisible(false);
      // Resume specific thread
      router.push({ pathname: "/(tabs)/stryda", params: { session_id: thread.session_id }});
  };

  const recentHistory = [
    "E2/AS1 Sill Flashing requirements",
    "NZS 3604 Bracing calculations",
    "H1 insulation schedule method"
  ];

  return (
    <SafeAreaView className="flex-1 bg-stryda-dark">
      {/* Recent Chats Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View className="flex-1 justify-end bg-black/50">
          <View className="bg-neutral-900 rounded-t-3xl max-h-[80%] border-t border-neutral-700">
            {/* Modal Header */}
            <View className="flex-row justify-between items-center p-5 border-b border-neutral-800">
              <Text className="text-white text-xl font-bold">Recent Chats</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)} className="p-2 bg-neutral-800 rounded-full">
                <X size={20} color="#999" />
              </TouchableOpacity>
            </View>
            
            {loading ? (
              <View className="p-10">
                  <ActivityIndicator color="#FF6B00" size="large" />
              </View>
            ) : (
              <View>
                  <FlatList
                    data={threads}
                    keyExtractor={(item) => item.session_id}
                    contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 10, paddingTop: 10 }}
                    style={{ maxHeight: 400 }}
                    ListEmptyComponent={
                      <View className="items-center py-10">
                        <Text className="text-neutral-400 mb-3">No recent chats found</Text>
                        <TouchableOpacity onPress={loadThreads} className="bg-neutral-800 px-4 py-2 rounded-full">
                           <Text className="text-white font-medium text-sm">Retry Loading</Text>
                        </TouchableOpacity>
                      </View>
                    }
                    renderItem={({ item }) => (
                      <TouchableOpacity 
                        className="p-4 mb-3 rounded-xl bg-neutral-800 border border-neutral-700 flex-row justify-between items-center"
                        onPress={() => handleThreadSelect(item)}
                      >
                        <View className="flex-1 mr-4">
                            <Text className="text-white font-bold text-lg mb-1" numberOfLines={1}>{item.title || "Untitled Chat"}</Text>
                            <View className="flex-row items-center">
                                <View className={`px-2 py-0.5 rounded-md mr-2 ${item.project_name ? 'bg-blue-900/30' : 'bg-neutral-700'}`}>
                                    <Text className={`text-xs font-medium ${item.project_name ? 'text-blue-400' : 'text-neutral-400'}`}>
                                        {item.project_name || "Unfiled"}
                                    </Text>
                                </View>
                                <Text className="text-neutral-500 text-xs" numberOfLines={1}>
                                    {item.preview_text || "No preview"}
                                </Text>
                            </View>
                        </View>
                        <ChevronRight size={20} color="#666" />
                      </TouchableOpacity>
                    )}
                  />

                  {/* Modal Footer Actions */}
                  <View className="p-5 border-t border-neutral-800 gap-3 pb-8">
                      <TouchableOpacity 
                        className="flex-row items-center justify-center bg-orange-600 p-4 rounded-xl shadow-sm"
                        onPress={() => {
                            setModalVisible(false);
                            handleNewChat();
                        }}
                      >
                          <Plus size={24} color="white" className="mr-2" />
                          <Text className="text-white font-bold text-lg">New Chat</Text>
                      </TouchableOpacity>
                  </View>
              </View>
            )}
          </View>
        </View>
      </Modal>

      <ScrollView className="flex-1 p-6">
        
        {/* Header - Chat Switcher */}
        <View className="flex-row justify-between items-center mb-8">
          <View>
            <Text className="text-neutral-400 text-sm font-medium">Kia Ora, Builder</Text>
            
            <TouchableOpacity 
              className="flex-row items-center mt-1"
              onPress={() => {
                loadThreads(); // Refresh on open
                setModalVisible(true);
              }}
              hitSlop={{ top: 20, bottom: 20, left: 20, right: 50 }}
            >
              <Text className="text-white text-xl font-bold mr-2">Recent Chats</Text>
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
          <Link href={{ pathname: "/(tabs)/stryda", params: { initialQuery: "I need to verify something on site. What details do you need?" }}} asChild>
            <TouchableOpacity className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between">
              <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
                <Camera size={24} color="#FF6B00" />
              </View>
              <Text className="text-white text-lg font-bold">Quick Verify</Text>
            </TouchableOpacity>
          </Link>

          {/* Card 2: Wind Zones */}
          <Link href="/(tabs)/wind" asChild>
            <TouchableOpacity className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between">
              <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
                <Map size={24} color="#FF6B00" />
              </View>
              <Text className="text-white text-lg font-bold">Wind Zones</Text>
            </TouchableOpacity>
          </Link>

          {/* Card 3: Bracing Calc */}
          <Link href={{ pathname: "/(tabs)/stryda", params: { initialQuery: "I need to calculate bracing. What details do you need?" }}} asChild>
            <TouchableOpacity className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between">
              <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
                <Calculator size={24} color="#FF6B00" />
              </View>
              <Text className="text-white text-lg font-bold">Bracing Calc</Text>
            </TouchableOpacity>
          </Link>

          {/* Card 4: Flashings */}
          <Link href={{ pathname: "/(tabs)/stryda", params: { initialQuery: "Show me the E2/AS1 selection tables (Table 7) for flashings" }}} asChild>
            <TouchableOpacity className="w-[48%] bg-neutral-800 p-4 rounded-2xl border border-neutral-700 h-40 justify-between">
              <View className="bg-neutral-700/50 w-12 h-12 rounded-full items-center justify-center">
                <Grid size={24} color="#FF6B00" />
              </View>
              <Text className="text-white text-lg font-bold">Flashings</Text>
            </TouchableOpacity>
          </Link>
        </View>

        {/* Recent Questions List (Legacy - Keep as requested) */}
        <Text className="text-white text-lg font-bold mt-8 mb-4">Suggested Questions</Text>
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
