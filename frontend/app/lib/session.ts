import AsyncStorage from "@react-native-async-storage/async-storage";
import { v4 as uuid } from "uuid";

const KEY = "stryda.session_id";

export async function getSessionId(): Promise<string> {
  const existing = await AsyncStorage.getItem(KEY);
  if (existing) return existing;
  const id = uuid();
  await AsyncStorage.setItem(KEY, id);
  return id;
}