import type { KaniState } from "@/kanpai/state";

// ===== kani models =====
export enum ChatRole {
  system = "system",
  user = "user",
  assistant = "assistant",
  function = "function",
}

export enum RunState {
  stopped = "stopped",
  running = "running",
  waiting = "waiting",
  errored = "errored",
}

export interface FunctionCall {
  name: string;
  arguments: string;
}

export interface ChatMessage {
  role: ChatRole;
  content: string | null;
  name: string | null;
  function_call: FunctionCall | null;
}

// ===== kanpai ws =====
export interface WSMessage {
  type: string;
}

// ---- server events ----
export interface WSError extends WSMessage {
  msg: string;
}

export interface KaniSpawn extends WSMessage, KaniState {}

export interface KaniStateChange extends WSMessage {
  id: string;
  state: RunState;
}

export interface KaniMessage extends WSMessage {
  id: string;
  msg: ChatMessage;
}

export interface RootMessage extends WSMessage {
  msg: ChatMessage;
}

// ---- client events ----
export interface SendMessage extends WSMessage {
  type: "send_message";
  content: string;
}
