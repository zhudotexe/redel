import type { ChatMessage, RunState } from "@/kanpai/models";

export interface KaniState {
  id: string;
  parent: string | null;
  children: string[];
  always_included_messages: ChatMessage[];
  chat_history: ChatMessage[];
  state: RunState;
}

export interface AppState {
  kanis: KaniState[];
}
