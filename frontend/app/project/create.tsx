import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useState } from "react";
import { ChevronLeft, MapPin, Briefcase } from "lucide-react-native";
import { createProject } from "../../src/internal/lib/api";

export default function CreateProjectScreen() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) {
        Alert.alert("Required", "Please enter a project name.");
        return;
    }

    setLoading(true);
    try {
        const project = await createProject(name, address);
        Alert.alert("Success", "Project created successfully!");
        
        // Navigate to the new project
        router.replace({ pathname: "/project/[id]", params: { id: project.id } });
    } catch (e) {
        Alert.alert("Error", "Failed to create project. Please try again.");
    } finally {
        setLoading(false);
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-stryda-dark">
      {/* Header */}
      <View className="px-6 py-4 border-b border-neutral-800 flex-row items-center">
          <TouchableOpacity onPress={() => router.back()} className="mr-4">
              <ChevronLeft size={28} color="white" />
          </TouchableOpacity>
          <Text className="text-white text-xl font-bold">New Project</Text>
      </View>

      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"} 
        className="flex-1"
      >
        <ScrollView className="flex-1 p-6">
            <Text className="text-neutral-400 mb-6">Create a container for your site photos, chats, and documents.</Text>

            <View className="gap-6">
                {/* Name Input */}
                <View>
                    <Text className="text-white font-bold mb-2 ml-1">Project Name</Text>
                    <View className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 flex-row items-center">
                        <Briefcase size={20} color="#666" className="mr-3" />
                        <TextInput 
                            className="flex-1 text-white text-base"
                            placeholder="e.g. Queen St Reno"
                            placeholderTextColor="#555"
                            value={name}
                            onChangeText={setName}
                            autoFocus
                        />
                    </View>
                </View>

                {/* Address Input */}
                <View>
                    <Text className="text-white font-bold mb-2 ml-1">Site Address (Optional)</Text>
                    <View className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 flex-row items-center">
                        <MapPin size={20} color="#666" className="mr-3" />
                        <TextInput 
                            className="flex-1 text-white text-base"
                            placeholder="e.g. 123 Queen St, Auckland"
                            placeholderTextColor="#555"
                            value={address}
                            onChangeText={setAddress}
                        />
                    </View>
                </View>
            </View>

            {/* Create Button */}
            <TouchableOpacity 
                className={`mt-10 p-4 rounded-xl flex-row justify-center items-center ${loading ? 'bg-orange-800' : 'bg-orange-600'}`}
                onPress={handleCreate}
                disabled={loading}
            >
                {loading ? (
                    <ActivityIndicator color="white" />
                ) : (
                    <Text className="text-white font-bold text-lg">Create Project</Text>
                )}
            </TouchableOpacity>

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
