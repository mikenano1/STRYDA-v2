import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, ActivityIndicator, Alert, Modal, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Send, FileText, ChevronRight, Mic, Square, MoreVertical, X, Plus, Check, Edit2, Trash2 } from 'lucide-react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { chatAPI, Citation, getProjects, assignThreadToProject, getThreadDetails, updateThread, deleteThread, Project, Thread } from '../../src/internal/lib/api';
import { Audio } from 'expo-av';
import ChatMessageComponent from '../../src/internal/components/ChatMessage';

console.log("🚀 STRYDA CHAT v3.0 - CHAT SETTINGS ENABLED");

type Message = { id: string; role: 'user' | 'assistant'; text: string; citations?: Citation[]; loading?: boolean; error?: boolean; ts: number; };

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
  const [settingsModalVisible, setSettingsModalVisible] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  
  // Edit State
  const [editTitle, setEditTitle] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

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

  const openSettingsModal = async () => {
      setSettingsModalVisible(true);
      setEditTitle(currentThread?.title || "New Chat");
      setSelectedProjectId(currentThread?.project_id || null);
      
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

  const handleSaveChanges = async () => {
      try {
          const updated = await updateThread(sessionIdRef.current, {
              title: editTitle,
              project_id: selectedProjectId || undefined
          });
          
          setCurrentThread(prev => prev ? { 
              ...prev, 
              title: updated.title,
              project_name: updated.project_name, 
              project_id: updated.project_id 
          } : { 
              session_id: sessionIdRef.current, 
              title: updated.title, 
              project_name: updated.project_name, 
              project_id: updated.project_id 
          });
          
          setSettingsModalVisible(false);
          Alert.alert("Success", "Chat updated successfully");
      } catch (e) {
          Alert.alert("Error", "Failed to update chat");
      }
  };

  const handleDeleteChat = async () => {
      Alert.alert(
          "Delete Chat",
          "Are you sure? This cannot be undone.",
          [
              { text: "Cancel", style: "cancel" },
              { 
                  text: "Delete", 
                  style: "destructive", 
                  onPress: async () => {
                      console.log(`🗑️ User confirmed delete for session: ${sessionIdRef.current}`);
                      try {
                          await deleteThread(sessionIdRef.current);
                          console.log(`✅ Delete successful, navigating home`);
                          setSettingsModalVisible(false);
                          router.replace("/(tabs)/");
                      } catch(e) {
                          console.error(`❌ Delete failed:`, e);
                          Alert.alert("Error", `Failed to delete chat: ${e}`);
                      }
                  }
              }
          ]
      );
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
          const API_BASE_URL = Platform.OS === 'web' ? '' : 'https://rag-scraper.preview.emergentagent.com';
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

    const userMsg: Message = { id: Date.now().toString(), role: 'user', text: textToSend, ts: Date.now() };
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
        citations: response.citations,
        ts: Date.now()
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', text: "Error connecting to backend.", error: true, ts: Date.now() }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler to navigate to PDF viewer
  const handleOpenDocument = (source: string, clause: string, page: string, filePath: string) => {
      console.log(`📄 Navigating to PDF Viewer: ${source} | Clause ${clause} | Page ${page}`);
      router.push({
          pathname: '/pdf-viewer',
          params: { source, clause, page, filePath }
      });
  };

  const renderItem = ({ item }: { item: Message }) => {
    return (
      <ChatMessageComponent 
        message={item} 
        onCitationPress={() => {}} 
        onOpenDocument={handleOpenDocument}
        onRetry={() => handleSend(item.text)}
      />
    );
  };

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
          <TouchableOpacity onPress={openSettingsModal} className="p-2 bg-neutral-800 rounded-full border border-neutral-700">
              <MoreVertical size={20} color="#9CA3AF" />
          </TouchableOpacity>
      </View>

      <FlatList 
        ref={flatListRef} 
        data={messages} 
        renderItem={renderItem} 
        keyExtractor={i => i.id} 
        contentContainerStyle={{ padding: 16 }} 
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        keyboardShouldPersistTaps="handled"
        removeClippedSubviews={false}
      />
      
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

      {/* Chat Settings Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={settingsModalVisible}
        onRequestClose={() => setSettingsModalVisible(false)}
      >
        <View className="flex-1 justify-end bg-black/50">
          <View className="bg-neutral-900 rounded-t-3xl max-h-[90%] border-t border-neutral-700">
            <View className="flex-row justify-between items-center p-5 border-b border-neutral-800">
              <Text className="text-white text-xl font-bold">Chat Settings</Text>
              <TouchableOpacity onPress={() => setSettingsModalVisible(false)} className="p-2 bg-neutral-800 rounded-full">
                <X size={20} color="#999" />
              </TouchableOpacity>
            </View>
            
            <ScrollView contentContainerStyle={{ padding: 20 }}>
                {/* Section 1: Rename */}
                <Text className="text-neutral-400 text-xs font-bold uppercase mb-2">Rename Chat</Text>
                <View className="bg-neutral-800 rounded-xl p-4 mb-6 border border-neutral-700 flex-row items-center">
                    <Edit2 size={18} color="#666" className="mr-3" />
                    <TextInput 
                        className="flex-1 text-white font-medium text-base"
                        value={editTitle}
                        onChangeText={setEditTitle}
                        placeholder="Chat Title"
                        placeholderTextColor="#555"
                    />
                </View>

                {/* Section 2: Assign Project */}
                <Text className="text-neutral-400 text-xs font-bold uppercase mb-2">Assign to Project</Text>
                {loadingProjects ? (
                    <ActivityIndicator color="#FF6B00" />
                ) : (
                    <View className="bg-neutral-800 rounded-xl border border-neutral-700 overflow-hidden mb-6">
                        <TouchableOpacity 
                            className="p-4 border-b border-neutral-700 bg-orange-600/10 flex-row items-center"
                            onPress={() => {
                                setSettingsModalVisible(false);
                                router.push('/project/create');
                            }}
                        >
                            <Plus size={18} color="#F97316" className="mr-3" />
                            <Text className="text-orange-500 font-bold">Create New Project</Text>
                        </TouchableOpacity>
                        
                        {projects.map((project) => (
                            <TouchableOpacity 
                                key={project.id}
                                className={`p-4 border-b border-neutral-700 flex-row justify-between items-center ${selectedProjectId === project.id ? 'bg-blue-900/20' : ''}`}
                                onPress={() => setSelectedProjectId(project.id)}
                            >
                                <Text className={`font-medium ${selectedProjectId === project.id ? 'text-blue-400' : 'text-neutral-300'}`}>{project.name}</Text>
                                {selectedProjectId === project.id && <Check size={18} color="#3B82F6" />}
                            </TouchableOpacity>
                        ))}
                        
                        <TouchableOpacity 
                            className={`p-4 flex-row justify-between items-center ${selectedProjectId === null ? 'bg-blue-900/20' : ''}`}
                            onPress={() => setSelectedProjectId(null)}
                        >
                            <Text className={`font-medium ${selectedProjectId === null ? 'text-blue-400' : 'text-neutral-300'}`}>Unfiled (No Project)</Text>
                            {selectedProjectId === null && <Check size={18} color="#3B82F6" />}
                        </TouchableOpacity>
                    </View>
                )}

                {/* Section 3: Actions */}
                <TouchableOpacity 
                    className="bg-orange-600 p-4 rounded-xl items-center mb-3"
                    onPress={handleSaveChanges}
                >
                    <Text className="text-white font-bold text-lg">Save Changes</Text>
                </TouchableOpacity>

                <TouchableOpacity 
                    className="bg-red-500/10 p-4 rounded-xl items-center border border-red-500/30 flex-row justify-center"
                    onPress={handleDeleteChat}
                >
                    <Trash2 size={18} color="#EF4444" className="mr-2" />
                    <Text className="text-red-500 font-bold text-lg">Delete Chat</Text>
                </TouchableOpacity>

            </ScrollView>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}
