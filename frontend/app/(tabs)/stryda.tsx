import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Send, FileText, ChevronRight } from 'lucide-react-native'; // Removed Mic
import { useLocalSearchParams, useRouter } from 'expo-router';
import { chatAPI, Citation } from '../../src/internal/lib/api';

console.log("🚀 STRYDA CHAT v3.0 - SAFE MODE LOADED");

// --- INLINED HELPER (Fixes the "Missing Module" error) ---
const getPdfUrl = (citationTitle: string | null): { url: string; title: string } | null => {
  if (!citationTitle) return null;
  const lowerTitle = citationTitle.toLowerCase();
  if (lowerTitle.includes('e2/as1') || lowerTitle.includes('e2')) return { title: 'E2/AS1 (External Moisture)', url: 'https://codehub.building.govt.nz/assets/Approved-Documents/E2-External-moisture-3rd-edition-Amendment-10.pdf' };
  if (lowerTitle.includes('3604') || lowerTitle.includes('timber')) return { title: 'NZS 3604:2011 (Selected Extracts)', url: 'https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b1-structure/as1-nzs3604-2011-light-timber-framed-buildings.pdf' };
  return null;
};

type Message = { id: string; role: 'user' | 'assistant'; text: string; citations?: Citation[]; };

export default function StrydaChat() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);
  
  // Create a stable session ID
  const sessionIdRef = useRef(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    if (params.initialQuery) {
        // Adding a small delay to ensure UI is ready
        setTimeout(() => {
            handleSend(params.initialQuery as string);
        }, 500);
        router.setParams({ initialQuery: '' });
    }
  }, [params.initialQuery]);

  const handleSend = async (textOverride?: string) => {
    const textToSend = textOverride || input;
    if (!textToSend.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', text: textToSend };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      console.log("Sending message...", textToSend);
      const response = await chatAPI({
          session_id: sessionIdRef.current,
          message: textToSend
      });
      console.log("Received response:", response);
      
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        text: response.message || "I couldn't process that response.",
        citations: response.citations
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', text: "Error connecting to backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderItem = ({ item }: { item: Message }) => (
    <View className={`mb-4 w-full flex-row ${item.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <View className={`max-w-[85%] p-4 ${item.role === 'user' ? 'bg-orange-600 rounded-2xl rounded-tr-sm' : 'bg-neutral-800 rounded-2xl rounded-tl-sm'}`}>
        <Text className={`${item.role === 'user' ? 'text-white' : 'text-neutral-200'} text-base leading-6`}>{item.text}</Text>
        {item.citations?.map((cite, i) => (
          <TouchableOpacity key={i} onPress={() => {
             const data = getPdfUrl(cite.source);
             if(data) router.push({ pathname: '/pdf-viewer', params: { url: data.url, title: data.title } });
          }} className="mt-3 pt-3 border-t border-neutral-700 flex-row items-center">
            <FileText size={20} color="#F97316" />
            <Text className="text-orange-500 font-bold text-sm ml-2">{cite.source} {cite.clause}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  return (
    <SafeAreaView className="flex-1 bg-neutral-950" edges={['top']}>
      <FlatList ref={flatListRef} data={messages} renderItem={renderItem} keyExtractor={i => i.id} contentContainerStyle={{ padding: 16 }} />
      {isLoading && (
        <View className="flex-row justify-center py-4">
            <ActivityIndicator size="small" color="#F97316" style={{ marginBottom: 10 }} />
        </View>
      )}
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={90}>
        <View className="bg-neutral-900 border-t border-neutral-800 p-4 pb-8 flex-row items-end">
          <TextInput className="flex-1 bg-neutral-950 text-white rounded-xl px-4 py-3 min-h-[50px] border border-neutral-800 mr-2" placeholder="Ask STRYDA..." placeholderTextColor="#525252" multiline value={input} onChangeText={setInput} />
          <TouchableOpacity onPress={() => handleSend()} className={`w-12 h-12 rounded-full items-center justify-center ${input.trim() ? 'bg-orange-500' : 'bg-neutral-800'}`}>
            <Send size={24} color={input.trim() ? '#000' : '#525252'} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
