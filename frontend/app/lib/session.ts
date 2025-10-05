import AsyncStorage from "@react-native-async-storage/async-storage";
import { v4 as uuid } from "uuid";

const SESSION_KEY = "stryda.chat.session";

export async function getSessionId(): Promise<string> {
  try {
    const existing = await AsyncStorage.getItem(SESSION_KEY);
    if (existing) return existing;
    
    const id = uuid();
    await AsyncStorage.setItem(SESSION_KEY, id);
    console.log('🆕 Generated new session ID:', id.substring(0, 8) + '...');
    return id;
  } catch (error) {
    console.error('❌ Session ID error:', error);
    // Fallback to timestamp-based ID
    return `fallback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export async function clearSession(): Promise<string> {
  try {
    await AsyncStorage.removeItem(SESSION_KEY);
    const newId = await getSessionId();
    console.log('🗑️ Session cleared, new ID:', newId.substring(0, 8) + '...');
    return newId;
  } catch (error) {
    console.error('❌ Clear session error:', error);
    return await getSessionId();
  }
}