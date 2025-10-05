import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, FlatList, ActivityIndicator } from "react-native";
import { observer } from "mobx-react-lite";
import { chatStore } from "../state/chat";

const Pill = ({ c }: { c: any }) => (
  <TouchableOpacity style={{ paddingVertical:6, paddingHorizontal:10, borderRadius:16, backgroundColor:"#1a1a1a", marginRight:8, marginTop:8 }}>
    <Text style={{ color:"#fff" }}>{c.source} p.{c.page}</Text>
  </TouchableOpacity>
);

export default observer(function ChatScreen(){
  const [text, setText] = useState("");
  return (
    <View style={{ flex:1, backgroundColor:"#000", padding:16 }}>
      <FlatList
        data={chatStore.messages}
        keyExtractor={(_,i)=>String(i)}
        contentContainerStyle={{ paddingBottom:88 }}
        renderItem={({item})=>(
          <View style={{ marginBottom:12, alignSelf: item.role==="user" ? "flex-end":"flex-start", maxWidth:"90%" }}>
            <View style={{ backgroundColor:item.role==="user"?"#FF7A00":"#1a1a1a", padding:12, borderRadius:12 }}>
              <Text style={{ color:"#fff" }}>{item.text}</Text>
            </View>
            {item.citations?.length ? (
              <View style={{ flexDirection:"row", flexWrap:"wrap" }}>
                {item.citations.map((c:any, idx:number)=><Pill key={idx} c={c} />)}
              </View>
            ) : null}
          </View>
        )}
      />

      <View style={{ position:"absolute", left:0, right:0, bottom:0, padding:12, backgroundColor:"#000", borderTopWidth:1, borderTopColor:"#222" }}>
        <View style={{ flexDirection:"row", alignItems:"center", gap:8 }}>
          <TextInput
            value={text}
            onChangeText={setText}
            placeholder="Ask STRYDA…"
            placeholderTextColor="#777"
            style={{ flex:1, color:"#fff", backgroundColor:"#111", borderRadius:12, paddingHorizontal:12, paddingVertical:10 }}
          />
          <TouchableOpacity
            onPress={()=>{ if(!chatStore.loading && text.trim()){ chatStore.send(text.trim()); setText(""); } }}
            disabled={chatStore.loading || !text.trim()}
            style={{ backgroundColor: chatStore.loading ? "#333" : "#FF7A00", paddingHorizontal:16, paddingVertical:10, borderRadius:12 }}
          >
            {chatStore.loading ? <ActivityIndicator /> : <Text style={{ color:"#fff", fontWeight:"600" }}>Send</Text>}
          </TouchableOpacity>
        </View>
        {chatStore.lastError ? <Text style={{ color:"#f66", marginTop:6 }}>{chatStore.lastError}</Text> : null}
      </View>
    </View>
  );
});