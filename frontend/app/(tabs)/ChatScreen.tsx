import React, { useState, useEffect } from "react";
import { View, Text, TextInput, TouchableOpacity, FlatList, ActivityIndicator, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { observer } from "mobx-react-lite";
import { chatStore } from "../state/chat";

const CitationPill = ({ citation, onPress }: { citation: any; onPress: () => void }) => (
  <TouchableOpacity 
    style={{ 
      paddingVertical:6, 
      paddingHorizontal:10, 
      borderRadius:16, 
      backgroundColor:"#FF7A00", 
      marginRight:8, 
      marginTop:8 
    }}
    onPress={onPress}
    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
  >
    <Text style={{ color:"#000", fontSize: 12, fontWeight: "500" }}>
      {citation.source} p.{citation.page}
    </Text>
  </TouchableOpacity>
);

const MessageItem = observer(({ item }: { item: any }) => {
  const [expandedCitation, setExpandedCitation] = useState<any>(null);
  
  const handleCitationPress = (citation: any) => {
    setExpandedCitation(expandedCitation?.page === citation.page ? null : citation);
    console.log('[telemetry] citation_pill_opened', {
      source: citation.source,
      page: citation.page,
      score: citation.score
    });
  };
  
  return (
    <View style={{ marginBottom:16, alignSelf: item.role==="user" ? "flex-end":"flex-start", maxWidth:"85%" }}>
      <View style={{ 
        backgroundColor: item.role==="user" ? "#FF7A00" : "#1a1a1a", 
        padding: 12, 
        borderRadius: 16,
        borderBottomRightRadius: item.role==="user" ? 4 : 16,
        borderBottomLeftRadius: item.role==="assistant" ? 4 : 16
      }}>
        <Text style={{ 
          color: item.role==="user" ? "#000" : "#fff", 
          fontSize: 16,
          lineHeight: 22 
        }}>
          {item.text}
        </Text>
        
        {/* Debug timing in development */}
        {__DEV__ && item.timing_ms && item.role === "assistant" && (
          <Text style={{ color:"#888", fontSize: 10, marginTop: 4 }}>
            ({(item.timing_ms/1000).toFixed(1)}s)
          </Text>
        )}
      </View>
      
      {/* Citations */}
      {item.citations?.length > 0 && (
        <View style={{ flexDirection:"row", flexWrap:"wrap", marginTop: 8 }}>
          {item.citations.map((c:any, idx:number) => (
            <CitationPill 
              key={idx} 
              citation={c} 
              onPress={() => handleCitationPress(c)}
            />
          ))}
        </View>
      )}
      
      {/* Expanded citation */}
      {expandedCitation && (
        <View style={{ 
          backgroundColor: "#2a2a2a", 
          padding: 12, 
          borderRadius: 8, 
          marginTop: 8 
        }}>
          <Text style={{ color: "#FF7A00", fontSize: 14, fontWeight: "600", marginBottom: 8 }}>
            {expandedCitation.source} • Page {expandedCitation.page}
          </Text>
          
          {expandedCitation.snippet && (
            <Text style={{ color: "#ccc", fontSize: 14, lineHeight: 20, marginBottom: 8 }}>
              {expandedCitation.snippet}
            </Text>
          )}
          
          <View style={{ flexDirection: "row", flexWrap: "wrap" }}>
            {expandedCitation.score && (
              <Text style={{ color: "#888", fontSize: 12, marginRight: 12 }}>
                Relevance: {(expandedCitation.score * 100).toFixed(0)}%
              </Text>
            )}
            {expandedCitation.section && (
              <Text style={{ color: "#888", fontSize: 12, marginRight: 12 }}>
                Section: {expandedCitation.section.substring(0, 20)}...
              </Text>
            )}
            {expandedCitation.clause && (
              <Text style={{ color: "#888", fontSize: 12 }}>
                Clause: {expandedCitation.clause}
              </Text>
            )}
          </View>
        </View>
      )}
    </View>
  );
});

export default observer(function ChatScreen(){
  const [text, setText] = useState("");
  const flatListRef = React.useRef<FlatList>(null);
  
  // Bootstrap on mount
  useEffect(() => {
    chatStore.bootstrap();
  }, []);
  
  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (chatStore.messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [chatStore.messages.length]);
  
  const handleSend = () => {
    if (!chatStore.loading && text.trim()) {
      chatStore.send(text.trim());
      setText("");
    }
  };
  
  const handleNewChat = () => {
    Alert.alert(
      "New Chat",
      "Start a new conversation?",
      [
        { text: "Cancel", style: "cancel" },
        { text: "New Chat", onPress: () => chatStore.clear() }
      ]
    );
  };
  
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: "#000" }}>
      {/* Header */}
      <View style={{ 
        flexDirection: "row", 
        justifyContent: "space-between", 
        alignItems: "center",
        padding: 16,
        borderBottomWidth: 1,
        borderBottomColor: "#333"
      }}>
        <Text style={{ color: "#fff", fontSize: 20, fontWeight: "bold" }}>
          STRYDA.ai
        </Text>
        <TouchableOpacity 
          onPress={handleNewChat}
          style={{ 
            backgroundColor: "#FF7A00", 
            paddingHorizontal: 12, 
            paddingVertical: 6, 
            borderRadius: 12 
          }}
        >
          <Text style={{ color: "#000", fontSize: 14, fontWeight: "600" }}>
            New Chat
          </Text>
        </TouchableOpacity>
      </View>
      
      {/* Messages */}
      <View style={{ flex: 1, padding: 16 }}>
        {chatStore.messages.length === 0 ? (
          <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
            <Text style={{ color: "#888", fontSize: 16, textAlign: "center", marginBottom: 16 }}>
              Ask STRYDA about:
            </Text>
            <Text style={{ color: "#ccc", fontSize: 14, textAlign: "center" }}>
              • Flashing cover requirements{'\n'}
              • High wind zone standards{'\n'}
              • Metal roofing fixings{'\n'}
              • Building code compliance
            </Text>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={chatStore.messages}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => <MessageItem item={item} />}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 20 }}
          />
        )}
      </View>
      
      {/* Input */}
      <View style={{ 
        padding: 16, 
        backgroundColor: "#111", 
        borderTopWidth: 1, 
        borderTopColor: "#333"
      }}>
        <View style={{ flexDirection: "row", alignItems: "flex-end" }}>
          <TextInput
            value={text}
            onChangeText={setText}
            placeholder="Ask STRYDA…"
            placeholderTextColor="#777"
            multiline
            maxLength={1000}
            style={{ 
              flex: 1, 
              color: "#fff", 
              backgroundColor: "#222", 
              borderRadius: 20, 
              paddingHorizontal: 16, 
              paddingVertical: 12,
              marginRight: 12,
              minHeight: 44,
              maxHeight: 100,
              fontSize: 16
            }}
            editable={!chatStore.loading}
            onSubmitEditing={handleSend}
          />
          <TouchableOpacity
            onPress={handleSend}
            disabled={chatStore.loading || !text.trim()}
            style={{ 
              backgroundColor: (chatStore.loading || !text.trim()) ? "#555" : "#FF7A00", 
              paddingHorizontal: 20, 
              paddingVertical: 12, 
              borderRadius: 20,
              minHeight: 44,
              justifyContent: "center",
              alignItems: "center"
            }}
          >
            {chatStore.loading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={{ color: "#000", fontWeight: "600", fontSize: 16 }}>Send</Text>
            )}
          </TouchableOpacity>
        </View>
        
        {chatStore.lastError && (
          <View style={{ 
            backgroundColor: "#441", 
            padding: 8, 
            borderRadius: 8, 
            marginTop: 8 
          }}>
            <Text style={{ color: "#f66", fontSize: 14 }}>
              {chatStore.lastError}
            </Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
});