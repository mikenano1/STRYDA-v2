
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Plus, ArrowRight, Folder } from "lucide-react-native";
import { useRouter } from "expo-router";
import { useState, useEffect } from "react";
import { getProjects, Project } from "../../src/internal/lib/api";

export default function ProjectsScreen() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    try {
        const data = await getProjects();
        setProjects(data);
    } catch (e) {
        console.error(e);
    } finally {
        setLoading(false);
    }
  };

  const handleProjectPress = (project: Project) => {
      router.push({ pathname: "/project/[id]", params: { id: project.id } });
      // For now, just reload to refresh
      // loadProjects();
      // router.push(`/project/${project.id}`);
      router.push({ pathname: "/project/[id]", params: { id: project.id } });
  };

  return (
    <SafeAreaView className="flex-1 bg-stryda-dark">
      <View className="p-6 pb-2 flex-row justify-between items-center">
        <Text className="text-white text-3xl font-bold">My Projects</Text>
        <TouchableOpacity 
            className="bg-orange-600 p-3 rounded-full"
            onPress={() => console.log("New Project")}
        >
            <Plus size={24} color="white" />
        </TouchableOpacity>
      </View>

      <ScrollView className="flex-1 px-6 pt-4">
        {loading ? (
            <ActivityIndicator color="#FF6B00" size="large" className="mt-10" />
        ) : projects.length === 0 ? (
            <View className="items-center justify-center mt-20 p-6 bg-neutral-900 rounded-2xl border border-neutral-800">
                <Folder size={48} color="#525252" className="mb-4" />
                <Text className="text-white text-xl font-bold mb-2">No Projects Yet</Text>
                <Text className="text-neutral-400 text-center mb-6">Create your first project to start organizing your chats and documents.</Text>
                <TouchableOpacity className="bg-orange-600 px-6 py-3 rounded-xl">
                    <Text className="text-white font-bold">Create Project</Text>
                </TouchableOpacity>
            </View>
        ) : (
            <View className="gap-4 pb-10">
                {projects.map((project) => (
                    <TouchableOpacity 
                        key={project.id}
                        className="bg-neutral-900 p-5 rounded-2xl border border-neutral-800 active:border-orange-500/50"
                        onPress={() => handleProjectPress(project)}
                    >
                        <View className="flex-row justify-between items-start">
                            <View className="flex-1 mr-4">
                                <Text className="text-white text-xl font-bold mb-1">{project.name}</Text>
                                {project.address && (
                                    <Text className="text-neutral-400 text-sm mb-3">{project.address}</Text>
                                )}
                                <View className="flex-row items-center">
                                    <View className="bg-blue-900/30 px-2 py-1 rounded-md mr-2">
                                        <Text className="text-blue-400 text-xs font-bold">Active</Text>
                                    </View>
                                    <Text className="text-neutral-500 text-xs">Last active today</Text>
                                </View>
                            </View>
                            <View className="bg-neutral-800 p-2 rounded-full">
                                <ArrowRight size={20} color="#666" />
                            </View>
                        </View>
                    </TouchableOpacity>
                ))}
            </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
