import React, { useEffect, useState } from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';
import { API_BASE, pingHealth, pingChat } from './diag';

export default function DiagOverlay() {
  const [open, setOpen] = useState(true);
  const [health, setHealth] = useState<any>(null);
  const [chat, setChat] = useState<any>(null);

  async function run() {
    const h = await pingHealth();
    const c = await pingChat();
    setHealth(h); setChat(c);
    console.log('DIAG health:', h);
    console.log('DIAG chat:', c);
  }

  useEffect(() => { run(); }, []);

  if (!open) return (
    <Pressable onPress={() => setOpen(true)} style={{ position:'absolute', top:8, right:8, padding:8, backgroundColor:'#222', borderRadius:8 }}>
      <Text style={{ color:'#fff' }}>Diag</Text>
    </Pressable>
  );

  return (
    <View style={{ position:'absolute', top:8, left:8, right:8, padding:10, backgroundColor:'#111', borderRadius:10, borderWidth:1, borderColor:'#333' }}>
      <View style={{ flexDirection:'row', justifyContent:'space-between', marginBottom:6 }}>
        <Text style={{ color:'#fff', fontWeight:'600' }}>Diagnostics</Text>
        <Pressable onPress={() => setOpen(false)}><Text style={{ color:'#aaa' }}>hide</Text></Pressable>
      </View>
      <Text style={{ color:'#bbb', marginBottom:4 }}>API_BASE: {API_BASE}</Text>
      <ScrollView style={{ maxHeight:160 }}>
        <Text style={{ color:'#7df' }}>Health → ok:{String(health?.ok)} status:{health?.status} ms:{health?.ms}</Text>
        <Text style={{ color:'#aaa' }} selectable>{health?.text}</Text>
        <Text style={{ color:'#7df', marginTop:8 }}>Chat → ok:{String(chat?.ok)} status:{chat?.status} ms:{chat?.ms}</Text>
        <Text style={{ color:'#aaa' }} selectable>{chat?.text}</Text>
      </ScrollView>
    </View>
  );
}