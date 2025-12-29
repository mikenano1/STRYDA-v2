import { View, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function ProjectsScreen() {
  return (
    <SafeAreaView className="flex-1 bg-stryda-dark">
      <View className="p-6">
        <Text className="text-white text-2xl font-bold">Projects</Text>
        <Text className="text-neutral-400 mt-2">Saved sites will appear here.</Text>
      </View>
    </SafeAreaView>
  );
}
