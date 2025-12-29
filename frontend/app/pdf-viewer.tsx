import { View, Text, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { WebView } from 'react-native-webview';
import { ChevronLeft } from 'lucide-react-native';
import { useState } from 'react';

export default function PdfViewer() {
  const router = useRouter();
  const { url, title } = useLocalSearchParams<{ url: string; title: string }>();
  const [loading, setLoading] = useState(true);

  if (!url) {
    return (
      <SafeAreaView className="flex-1 bg-neutral-950 justify-center items-center">
        <Text className="text-white">No document URL provided.</Text>
        <TouchableOpacity onPress={() => router.back()} className="mt-4 bg-orange-600 px-4 py-2 rounded-lg">
          <Text className="text-white font-bold">Go Back</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  // Google Docs Viewer fallback for Android or generic web view stability
  // Note: Direct PDF links often fail in plain WebViews on Android
  const viewerUrl = `https://docs.google.com/gview?embedded=true&url=${encodeURIComponent(url)}`;

  return (
    <SafeAreaView className="flex-1 bg-neutral-950" edges={['top']}>
      {/* Header */}
      <View className="flex-row items-center p-4 border-b border-neutral-800 bg-neutral-900">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <ChevronLeft size={28} color="white" />
        </TouchableOpacity>
        <Text className="text-white text-lg font-bold flex-1" numberOfLines={1}>
          {title || 'Document Viewer'}
        </Text>
      </View>

      {/* WebView */}
      <View className="flex-1 bg-white relative">
        {loading && (
          <View className="absolute inset-0 justify-center items-center z-10 bg-neutral-900">
            <ActivityIndicator size="large" color="#FF6B00" />
            <Text className="text-neutral-400 mt-2">Loading Document...</Text>
          </View>
        )}
        <WebView
          source={{ uri: viewerUrl }}
          className="flex-1"
          onLoadEnd={() => setLoading(false)}
          startInLoadingState={true}
          renderLoading={() => <View />} // Handled by custom loader
        />
      </View>
    </SafeAreaView>
  );
}
