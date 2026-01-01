import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, ActivityIndicator, Alert, Modal } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Send, FileText, ChevronRight, Mic, Square, Folder, X, Plus, Check } from 'lucide-react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { chatAPI, Citation, getProjects, assignThreadToProject, getThreadDetails, Project, Thread } from '../../src/internal/lib/api';
import { Audio } from 'expo-av';

console.log("🚀 STRYDA CHAT v3.0 - FILE TO PROJECT ENABLED");

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
  
  // Voice State
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);

  // Thread & Project State
  const flatListRef = useRef<FlatList>(null);
  const sessionIdRef = useRef(
      params.session_id 
        ? (params.session_id as string) 
        : `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  
  const [currentThread, setCurrentThread] = useState<Thread | null>(null);
  const [assignModalVisible, setAssignModalVisible] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);

  useEffect(() => {
    if (params.session_id && params.session_id !== sessionIdRef.current) {
        console.log("🔄 Switching to session:", params.session_id);
        sessionIdRef.current = params.session_id as string;
        setMessages([]); 
        fetchThreadDetails();
    } else if (params.session_id) {
        // Initial load with session
        fetchThreadDetails();
    }

    if (params.initialQuery) {
        setTimeout(() => {
            handleSend(params.initialQuery as string);
        }, 500);
        router.setParams({ initialQuery: '' });
    }
  }, [params.initialQuery, params.session_id]);

  const fetchThreadDetails = async () => {
      const details = await getThreadDetails(sessionIdRef.current);
      if (details) {
          console.log("✅ Loaded thread details:", details.title);
          setCurrentThread(details);
      }
  };

  const openAssignModal = async () => {
      setAssignModalVisible(true);
      setLoadingProjects(true);
      try {
          const data = await getProjects();
          setProjects(data);
      } catch (e) {
          console.error("Failed to load projects", e);
      } finally {
          setLoadingProjects(false);
      }
  };

  const handleAssignProject = async (project: Project) => {
      try {
          // Optimistic update
          const updated = await assignThreadToProject(sessionIdRef.current, project.id);
          setAssignModalVisible(false);
          setCurrentThread(prev => prev ? { ...prev, project_name: project.name, project_id: project.id } : { 
              session_id: sessionIdRef.current, 
              title: updated.title, 
              project_name: project.name, 
              project_id: project.id 
          });
          Alert.alert("Saved", `Chat filed to ${project.name}`);
      } catch (e) {
          Alert.alert("Error", "Failed to assign project");
      }
  };

  // --- AUDIO LOGIC ---
  async function startRecording() {
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (permission.status === 'granted') {
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,
          playsInSilentModeIOS: true,
        });
        
        const { recording } = await Audio.Recording.createAsync(
           Audio.RecordingOptionsPresets.HIGH_QUALITY
        );
        setRecording(recording);
        setIsRecording(true);
      } else {
        Alert.alert("Permission required", "Please grant microphone permission to use voice.");
      }
    } catch (err) {
      console.error('Failed to start recording', err);
    }
  }

  async function stopRecording() {
    if (!recording) return;
    setIsRecording(false);
    
    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI(); 
      setRecording(null); 
      
      if(uri) await uploadAudio(uri);
    } catch(err) {
        console.error('Failed to stop recording', err);
    }
  }

  async function uploadAudio(uri: string) {
      setIsTranscribing(true);
      
      const formData = new FormData();
      formData.append('file', {
          uri: Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
          type: 'audio/m4a',
          name: 'recording.m4a'
      } as any);

      try {
          const API_BASE_URL = Platform.OS === 'web' ? '' : 'https://wind-calc.preview.emergentagent.com';
          const targetUrl = `${API_BASE_URL.replace(/\/$/, "")}/api/transcribe`;
          
          const response = await fetch(targetUrl, {
              method: 'POST',
              body: formData,
          });
          
          if (!response.ok) throw new Error('Server error');

          const data = await response.json();
          if(data.text) {
              setInput(prev => (prev ? prev + " " + data.text : data.text));
          }
      } catch (e) {
          Alert.alert("Transcription Failed", "Sorry, I couldn't hear that properly.");
      } finally {
          setIsTranscribing(false);
      }
  }

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
      
      // Update thread details if this was the first message
      if (!currentThread) fetchThreadDetails();
      
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
      {/* Header */}
      <View className="flex-row items-center justify-between px-4 py-3 border-b border-neutral-800 bg-neutral-900">
          <View className="flex-1">
              <Text className="text-white font-bold text-lg" numberOfLines={1}>
                  {currentThread?.title || "New Chat"}
              </Text>
              <View className="flex-row items-center">
                  <View className={`w-2 h-2 rounded-full mr-2 ${currentThread?.project_name ? 'bg-blue-500' : 'bg-neutral-500'}`} />
                  <Text className="text-neutral-400 text-xs">
                      {currentThread?.project_name || "Unfiled"}
                  </Text>
              </View>
          </View>
          <TouchableOpacity onPress={openAssignModal} className="p-2 bg-neutral-800 rounded-full border border-neutral-700">
              <Folder size={20} color={currentThread?.project_name ? "#3B82F6" : "#9CA3AF"} />
          </TouchableOpacity>
      </View>

      <FlatList ref={flatListRef} data={messages} renderItem={renderItem} keyExtractor={i => i.id} contentContainerStyle={{ padding: 16 }} />
      
      {isLoading && (
        <View className="flex-row justify-center py-4">
            <ActivityIndicator size="small" color="#F97316" style={{ marginBottom: 10 }} />
        </View>
      )}
      
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={90}>
        <View className="bg-neutral-900 border-t border-neutral-800 p-4 pb-8 flex-row items-end">
          <TextInput 
            className="flex-1 bg-neutral-950 text-white rounded-xl px-4 py-3 min-h-[50px] border border-neutral-800 mr-2" 
            placeholder={isRecording ? "Listening..." : (isTranscribing ? "Transcribing..." : "Ask STRYDA...")}
            placeholderTextColor={isRecording ? "#F97316" : "#525252"} 
            multiline 
            value={input} 
            onChangeText={setInput} 
            editable={!isRecording && !isTranscribing}
          />
          {input.trim().length > 0 ? (
             <TouchableOpacity onPress={() => handleSend()} className="w-12 h-12 rounded-full bg-orange-500 items-center justify-center">
                <Send size={24} color="#000" />
             </TouchableOpacity>
          ) : (
             <TouchableOpacity 
                onPress={isRecording ? stopRecording : startRecording} 
                className={`w-12 h-12 rounded-full items-center justify-center ${isRecording ? 'bg-red-500 animate-pulse' : (isTranscribing ? 'bg-neutral-700' : 'bg-neutral-800')}`}
                disabled={isTranscribing}
             >
                {isTranscribing ? <ActivityIndicator size="small" color="#FFF" /> : isRecording ? <Square size={20} color="#FFF" fill="white" /> : <Mic size={24} color="#F97316" />}
             </TouchableOpacity>
          )}
        </View>
      </KeyboardAvoidingView>

      {/* Assign Project Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={assignModalVisible}
        onRequestClose={() => setAssignModalVisible(false)}
      >
        <View className="flex-1 justify-end bg-black/50">
          <View className="bg-neutral-900 rounded-t-3xl max-h-[70%] border-t border-neutral-700">
            <View className="flex-row justify-between items-center p-5 border-b border-neutral-800">
              <Text className="text-white text-xl font-bold">Save Chat to Project</Text>
              <TouchableOpacity onPress={() => setAssignModalVisible(false)} className="p-2 bg-neutral-800 rounded-full">
                <X size={20} color="#999" />
              </TouchableOpacity>
            </View>
            
            {loadingProjects ? (
              <View className="p-10"><ActivityIndicator color="#FF6B00" size="large" /></View>
            ) : (
              <FlatList
                data={projects}
                keyExtractor={(item) => item.id}
                contentContainerStyle={{ padding: 20 }}
                ListHeaderComponent={
                    <TouchableOpacity className="flex-row items-center p-4 mb-4 bg-orange-600/10 border border-orange-500/50 rounded-xl">
                        <Plus size={20} color="#F97316" className="mr-3" />
                        <Text className="text-orange-500 font-bold">Create New Project</Text>
                    </TouchableOpacity>
                }
                renderItem={({ item }) => (
                  <TouchableOpacity 
                    className={`p-4 mb-3 rounded-xl border flex-row justify-between items-center ${currentThread?.project_id === item.id ? 'bg-blue-900/20 border-blue-500' : 'bg-neutral-800 border-neutral-700'}`}
                    onPress={() => handleAssignProject(item)}
                  >
                    <View>
                        <Text className="text-white font-bold text-lg">{item.name}</Text>
                        {item.address && <Text className="text-neutral-400 text-sm">{item.address}</Text>}
                    </View>
                    {currentThread?.project_id === item.id && <Check size={20} color="#3B82F6" />}
                  </TouchableOpacity>
                )}
              />
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}
