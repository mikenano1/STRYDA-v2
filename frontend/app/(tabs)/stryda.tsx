import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Mic, Send, FileText, ChevronRight } from 'lucide-react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { chatAPI, Citation } from '../../src/internal/lib/api';

// --- 1. INLINED PDF HELPER (No Imports needed) ---
const getPdfUrl = (citationTitle: string | null): { url: string; title: string } | null => {
  if (!citationTitle) return null;
  const lowerTitle = citationTitle.toLowerCase();
  if (lowerTitle.includes('e2/as1') || lowerTitle.includes('e2')) {
    return { title: 'E2/AS1 (External Moisture)', url: 'https://codehub.building.govt.nz/assets/Approved-Documents/E2-External-moisture-3rd-edition-Amendment-10.pdf' };
  }
  if (lowerTitle.includes('3604') || lowerTitle.includes('timber')) {
    return { title: 'NZS 3604:2011 (Selected Extracts)', url: 'https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b1-structure/as1-nzs3604-2011-light-timber-framed-buildings.pdf' };
  }
  if (lowerTitle.includes('h1') || lowerTitle.includes('energy')) {
    return { title: 'H1/AS1 (Energy Efficiency)', url: 'https://www.building.govt.nz/assets/Uploads/building-code-compliance/h-energy-efficiency/h1-energy-efficiency/as1-h1-energy-efficiency-5th-edition-amendment-1.pdf' };
  }
  return null;
};

// --- 2. TYPES ---
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

  // Auto-Send Logic (from Dashboard)
  useEffect(() => {
    if (params.initialQuery) {
      const query = params.initialQuery as string;
      // We need to wait for layout/render before sending or just send immediately
      // Adding a small delay to ensure UI is ready
      setTimeout(() => {
          handleSend(query);
      }, 500);
      router.setParams({ initialQuery: '' }); // Clear param to prevent double-send
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
      // Call Centralized API
      // Using the function signature: chatAPI(request: ChatRequest)
      const response = await chatAPI({
          session_id: sessionIdRef.current,
          message: textToSend
      });
      
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant', // Changed from 'ai' to 'assistant' to match Message type
        text: response.message || "I couldn't process that response.",
        citations: response.citations
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error(error);
      const errorMsg: Message = { id: Date.now().toString(), role: 'assistant', text: "Sorry mate, having trouble connecting to the site server." };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const openPdf = (citation: Citation) => {
    // Citation has source, not title in our interface, but let's check
    // In api.ts: interface Citation { source: string; ... }
    const pdfData = getPdfUrl(citation.source);
    if (pdfData) {
      router.push({ pathname: '/pdf-viewer', params: { url: pdfData.url, title: pdfData.title } });
    } else {
      Alert.alert("Document Not Synced", "This document isn't in the mobile library yet.");
    }
  };

  // --- RENDER HELPERS ---
  const renderItem = ({ item }: { item: Message }) => (
    <View className={`mb-4 w-full flex-row ${item.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <View className={`max-w-[85%] p-4 ${item.role === 'user' ? 'bg-orange-600 rounded-2xl rounded-tr-sm' : 'bg-neutral-800 rounded-2xl rounded-tl-sm'}`}>
        <Text className={`${item.role === 'user' ? 'text-white' : 'text-neutral-200'} text-base leading-6`}>{item.text}</Text>
        
        {/* Citation Cards */}
        {item.citations && item.citations.length > 0 && (
          <View className="mt-3 pt-3 border-t border-neutral-700">
            {item.citations.map((cite, index) => (
              <TouchableOpacity key={index} onPress={() => openPdf(cite)} className="flex-row items-center bg-neutral-900 p-2 rounded border-l-4 border-orange-500 mb-2">
                <FileText size={20} color="#F97316" />
                <View className="ml-2 flex-1">
                  <Text className="text-orange-500 font-bold text-sm">{cite.source} {cite.clause ? `(${cite.clause})` : ''}</Text>
                  <Text className="text-neutral-500 text-xs">Tap to view document</Text>
                </View>
                <ChevronRight size={16} color="#525252" />
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>
    </View>
  );

  return (
    <SafeAreaView className="flex-1 bg-neutral-950" edges={['top']}>
      <View className="flex-1">
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderItem}
          keyExtractor={item => item.id}
          contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />
        {isLoading && (
          <View className="absolute bottom-24 left-0 right-0 items-center">
            <View className="bg-neutral-800 px-4 py-2 rounded-full flex-row items-center">
              <ActivityIndicator size="small" color="#F97316" />
              <Text className="text-neutral-400 ml-2 text-xs">Scanning NZBC...</Text>
            </View>
          </View>
        )}
      </View>

      {/* INPUT COCKPIT */}
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}>
        <View className="bg-neutral-900 border-t border-neutral-800 p-4 pb-8 flex-row items-end">
          <TextInput
            className="flex-1 bg-neutral-950 text-white rounded-xl px-4 py-3 min-h-[50px] max-h-[120px] text-base border border-neutral-800 mr-2"
            placeholder="Ask STRYDA..."
            placeholderTextColor="#525252"
            multiline
            value={input}
            onChangeText={setInput}
          />
          
          {/* SAFE MODE MIC BUTTON (Disabled for Expo Go) */}
          <TouchableOpacity 
            onPress={() => Alert.alert("Dev Build Required", "Voice features require a custom Development Build. They are disabled in Expo Go.")}
            className="w-12 h-12 bg-neutral-800 rounded-full items-center justify-center mr-2"
          >
            <Mic size={24} color="#525252" />
          </TouchableOpacity>

          <TouchableOpacity 
            onPress={() => handleSend()}
            disabled={!input.trim()}
            className={`w-12 h-12 rounded-full items-center justify-center ${input.trim() ? 'bg-orange-500' : 'bg-neutral-800'}`}
          >
            <Send size={24} color={input.trim() ? '#000' : '#525252'} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
