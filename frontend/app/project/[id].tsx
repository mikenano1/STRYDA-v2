import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useState, useEffect } from "react";
import { ChevronLeft, Edit, MessageSquare, MapPin } from "lucide-react-native";
import { getProjects, getThreads, Project, Thread } from "../../src/internal/lib/api";

export default function ProjectDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const [project, setProject] = useState<Project | null>(null);
  const [projectThreads, setProjectThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
        // Fetch project list to find this specific one (in lieu of a single GET endpoint for now)
        const projects = await getProjects();
        const found = projects.find(p => p.id === id);
        if (found) setProject(found);

        // Fetch all threads and filter (optimisation: backend should support filtering)
        const allThreads = await getThreads();
        const filtered = allThreads.filter(t => t.project_id === id);
        setProjectThreads(filtered);
        
    } catch (e) {
        console.error(e);
    } finally {
        setLoading(false);
    }
  };

  if (loading) {
      return (
          <SafeAreaView className="flex-1 bg-stryda-dark items-center justify-center">
              <ActivityIndicator color="#FF6B00" size="large" />
          </SafeAreaView>
      );
  }

  if (!project) {
      return (
          <SafeAreaView className="flex-1 bg-stryda-dark items-center justify-center p-6">
              <Text className="text-white text-xl">Project not found</Text>
              <TouchableOpacity onPress={() => router.back()} className="mt-4">
                  <Text className="text-orange-500">Go Back</Text>
              </TouchableOpacity>
          </SafeAreaView>
      );
  }

  return (
    <SafeAreaView className="flex-1 bg-stryda-dark">
      {/* Header */}
      <View className="px-6 py-4 border-b border-neutral-800 flex-row items-center">
          <TouchableOpacity onPress={() => router.back()} className="mr-4">
              <ChevronLeft size={28} color="white" />
          </TouchableOpacity>
          <View className="flex-1">
              <Text className="text-white text-xl font-bold" numberOfLines={1}>{project.name}</Text>
          </View>
          <TouchableOpacity>
              <Edit size={20} color="#999" />
          </TouchableOpacity>
      </View>

      <ScrollView className="flex-1 p-6">
          {/* Metadata Card */}
          <View className="bg-neutral-900 p-5 rounded-2xl border border-neutral-800 mb-8">
              <View className="flex-row items-center mb-3">
                  <MapPin size={18} color="#FF6B00" className="mr-2" />
                  <Text className="text-neutral-300 font-medium">{project.address || "No address provided"}</Text>
              </View>
              <View className="flex-row gap-2 mt-2">
                  <View className="bg-blue-900/30 px-3 py-1 rounded-full">
                      <Text className="text-blue-400 text-xs font-bold">Active</Text>
                  </View>
                  <View className="bg-neutral-800 px-3 py-1 rounded-full">
                      <Text className="text-neutral-400 text-xs">Created Jan 2025</Text>
                  </View>
              </View>
          </View>

          {/* Threads List */}
          <Text className="text-white text-lg font-bold mb-4">Project Threads</Text>
          
          {projectThreads.length === 0 ? (
              <View className="items-center py-10 bg-neutral-900/50 rounded-2xl border border-dashed border-neutral-800">
                  <Text className="text-neutral-500 mb-4">No conversations filed here yet.</Text>
                  <TouchableOpacity 
                    className="bg-neutral-800 px-4 py-2 rounded-full border border-neutral-700"
                    onPress={() => router.push("/(tabs)/stryda")}
                  >
                      <Text className="text-white text-sm font-medium">Start New Chat</Text>
                  </TouchableOpacity>
              </View>
          ) : (
              <View className="gap-3 pb-10">
                  {projectThreads.map((thread) => (
                      <TouchableOpacity 
                        key={thread.session_id}
                        className="bg-neutral-900 p-4 rounded-xl border border-neutral-800 flex-row items-center"
                        onPress={() => router.push({ pathname: "/(tabs)/stryda", params: { session_id: thread.session_id }})}
                      >
                          <View className="bg-neutral-800 p-3 rounded-full mr-4">
                              <MessageSquare size={20} color="#FF6B00" />
                          </View>
                          <View className="flex-1">
                              <Text className="text-white font-bold text-base mb-1" numberOfLines={1}>
                                  {thread.title || "Untitled Chat"}
                              </Text>
                              <Text className="text-neutral-500 text-xs" numberOfLines={1}>
                                  {thread.preview_text || "Tap to view conversation..."}
                              </Text>
                          </View>
                          <ChevronRight size={20} color="#666" />
                      </TouchableOpacity>
                  ))}
              </View>
          )}
      </ScrollView>
    </SafeAreaView>
  );
}
