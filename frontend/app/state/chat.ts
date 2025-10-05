import { makeAutoObservable } from "mobx";
import { sendChat } from "../lib/api/chat";
import { getSessionId } from "../lib/session";

export type ChatMsg = { role: "user"|"assistant"; text: string; citations?: any[]; at: number; };

class ChatStore {
  messages: ChatMsg[] = [];
  loading = false;
  lastError: string | null = null;

  constructor(){ makeAutoObservable(this); }

  async send(text: string) {
    this.lastError = null;
    const session = await getSessionId();
    this.messages.push({ role: "user", text, at: Date.now() });
    this.loading = true;
    const t0 = performance.now();
    try {
      const res = await sendChat(session, text);
      this.messages.push({ role: "assistant", text: res.message, citations: res.citations, at: Date.now() });
      this.logMetric("chat_ok", performance.now()-t0);
    } catch (e:any) {
      this.lastError = e?.message ?? "Unknown error";
      this.logMetric("chat_err", performance.now()-t0);
    } finally {
      this.loading = false;
    }
  }

  logMetric(name: string, ms: number) {
    console.log(`[telemetry] ${name} ${Math.round(ms)}ms`);
  }
}

export const chatStore = new ChatStore();