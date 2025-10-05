import { ENV } from "../../config/env";

export type Citation = { source: string; page: number; score?: number; snippet?: string };
export type ChatResponse = { message: string; citations: Citation[]; session_id: string; notes?: string[] };

export async function sendChat(sessionId: string, userText: string, signal?: AbortSignal): Promise<ChatResponse> {
  const res = await fetch(`${ENV.API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message: userText }),
    signal
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}