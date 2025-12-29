import { useState, useRef, useEffect } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  FlatList, 
  KeyboardAvoidingView, 
  Platform,
  ActivityIndicator,
  Keyboard,
  Alert
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Send, Mic, FileText, ChevronLeft, MicOff } from 'lucide-react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { chatAPI, Citation } from '@/src/internal/lib/api';
import { getPdfUrl } from '@/src/internal/utils/pdfMap';
import { useSpeechRecognitionEvent, useSpeechRecognitionEventEvent, SpeechRecognition } from 'expo-speech-recognition';

// --- Types ---
interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
}

// --- Components ---

const CitationCard = ({ citation, onPress }: { citation: Citation; onPress: () => void }) => (
  <TouchableOpacity 
    onPress={onPress}
    className="bg-neutral-900 border-l-4 border-orange-500 rounded-r-lg p-3 mt-3 mb-1 flex-row items-center"
  >
    <View className="bg-neutral-800 p-2 rounded-full mr-3">
      <FileText size={20} color="#FFA500" />
    </View>
    <View className="flex-1">
      <Text className="text-white font-bold text-sm">
        {citation.source} {citation.clause ? `(${citation.clause})` : ''}
      </Text>
      <Text className="text-neutral-400 text-xs truncate" numberOfLines={1}>
        {citation.section || `Page ${citation.page}`}
      </Text>
      <Text className="text-orange-500 text-[10px] font-bold mt-1 uppercase">Tap to View</Text>
    </View>
  </TouchableOpacity>
);

const MessageBubble = ({ message, onCitationPress }: { message: Message; onCitationPress: (c: Citation) => void }) => {
  const isUser = message.role === 'user';
  
  return (
    <View className={`w-full flex-row ${isUser ? 'justify-end' : 'justify-start'} mb-4 px-4`}>
      <View 
        className={`max-w-[85%] p-4 rounded-2xl ${
          isUser 
            ? 'bg-orange-600 rounded-tr-none' 
            : 'bg-neutral-800 rounded-tl-none'
        }`}
      >
        <Text className={`text-base leading-6 ${isUser ? 'text-white' : 'text-neutral-200'}`}>
          {message.text}
        </Text>

        {/* Render Citations if AI */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <View className="mt-2">
            {message.citations.map((cite, index) => (
              <CitationCard 
                key={index} 
                citation={cite} 
                onPress={() => onCitationPress(cite)} 
              />
            ))}
          </View>
        )}
      </View>
    </View>
  );
};

const LoadingIndicator = () => (
  <View className="flex-row items-center justify-start px-6 mb-4">
    <View className="bg-neutral-800 rounded-2xl rounded-tl-none p-4 flex-row items-center">
      <ActivityIndicator size="small" color="#FF6B00" />
      <Text className="text-neutral-400 ml-3 text-sm font-medium">
        Scanning NZBC...
      </Text>
    </View>
  </View>
);

// --- Main Screen ---

export default function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [isListening, setIsListening] = useState(false);
  const flatListRef = useRef<FlatList>(null);
  
  const router = useRouter();
  const { initialQuery } = useLocalSearchParams<{ initialQuery?: string }>();

  // Initialize Session
  useEffect(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
  }, []);

  // Auto-send if initialQuery exists
  useEffect(() => {
    if (initialQuery && sessionId && !isLoading && messages.length === 0) {
      // Small delay for smooth transition
      setTimeout(() => {
        handleSend(initialQuery);
      }, 500);
    }
  }, [initialQuery, sessionId]);

  // Voice Recognition Hook
  useSpeechRecognitionEvent("onSpeechResults", (event: any) => {
    if (event.value && event.value.length > 0) {
      const spokenText = event.value[0];
      setInputText(spokenText);
    }
  });

  const handleMicPress = async () => {
    if (isListening) {
      SpeechRecognition.stop();
      setIsListening(false);
      return;
    }

    // Request permissions
    const perms = await SpeechRecognition.requestPermissionsAsync();
    if (!perms.granted) {
      Alert.alert("Permission Denied", "We need microphone access to hear you.");
      return;
    }

    try {
      SpeechRecognition.start();
      setIsListening(true);
    } catch (e) {
      console.error("Speech start failed", e);
      Alert.alert("Error", "Could not start microphone.");
      setIsListening(false);
    }
  };

  const handleSend = async (textOverride?: string) => {
    const text = textOverride || inputText.trim();
    if (!text || isLoading) return;

    if (isListening) {
      SpeechRecognition.stop();
      setIsListening(false);
    }

    // 1. Add User Message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: text
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);
    Keyboard.dismiss();

    try {
      // 2. Call API
      const response = await chatAPI({
        session_id: sessionId,
        message: text
      });

      // 3. Add AI Message
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        text: response.answer || response.message || "I couldn't process that.", // Handle varying response keys
        citations: response.citations || []
      };

      setMessages(prev => [...prev, aiMsg]);

    } catch (error) {
      console.error('Chat Error:', error);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        text: "Connection error. Please check your internet and try again."
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const openPdf = (citation: Citation) => {
    const doc = getPdfUrl(citation.source);
    
    if (!doc || !doc.url) {
        Alert.alert("Document Unavailable", "We couldn't find a PDF for this citation.");
        return;
    }

    const title = `${doc.title || citation.source} ${citation.clause || ''}`;
    
    console.log('Opening PDF:', doc.url);
    router.push({
      pathname: '/pdf-viewer',
      params: { url: doc.url, title }
    });
  };

  return (
    <SafeAreaView className="flex-1 bg-neutral-950" edges={['top']}>
      {/* Messages List */}
      <FlatList
        ref={flatListRef}
        data={messages} 
        renderItem={({ item }) => <MessageBubble message={item} onCitationPress={openPdf} />}
        keyExtractor={item => item.id}
        contentContainerStyle={{ paddingVertical: 20, paddingBottom: 40 }}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        onLayout={() => flatListRef.current?.scrollToEnd({ animated: true })}
        ListFooterComponent={isLoading ? <LoadingIndicator /> : null}
        className="flex-1"
      />

      {/* The Cockpit (Input Bar) */}
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View className="bg-neutral-900 border-t border-neutral-800 p-4 pb-6 flex-row items-end space-x-3">
          
          {/* Text Input */}
          <View className={`flex-1 border rounded-2xl min-h-[50px] justify-center px-4 py-2 ${isListening ? 'bg-red-900/20 border-red-500' : 'bg-neutral-950 border-neutral-800'}`}>
            <TextInput
              className="text-white text-base max-h-32"
              placeholder={isListening ? "Listening..." : "Ask STRYDA..."}
              placeholderTextColor={isListening ? "#F87171" : "#525252"}
              multiline
              value={inputText}
              onChangeText={setInputText}
              editable={!isListening} // Lock input while listening
            />
          </View>

          {/* Send Button */}
          <TouchableOpacity 
            className={`w-12 h-12 rounded-full items-center justify-center ${inputText.trim() && !isListening ? 'bg-orange-600' : 'bg-neutral-800'}`}
            onPress={() => handleSend()}
            disabled={!inputText.trim() || isLoading || isListening}
          >
            <Send size={20} color={inputText.trim() && !isListening ? "white" : "#555"} className={inputText.trim() ? "ml-1" : ""} />
          </TouchableOpacity>

          {/* Mic Button */}
          <TouchableOpacity 
            className={`w-12 h-12 rounded-full items-center justify-center ${isListening ? 'bg-red-500' : 'bg-neutral-800'}`}
            onPress={handleMicPress}
          >
            {isListening ? (
              <MicOff size={22} color="white" />
            ) : (
              <Mic size={22} color="#A3A3A3" />
            )}
          </TouchableOpacity>

        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
