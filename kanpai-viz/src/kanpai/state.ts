import type { ChatMessage } from "@/kanpai/models";

export interface KaniState {
  id: string;
  parent: string | null;
  children: string[];
  always_included_messages: ChatMessage[];
  chat_history: ChatMessage[];
}

export interface AppState {
  kanis: KaniState[];
}
