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

export interface ToolCall {
  id: string;
  type: string;
  function: FunctionCall;
}

export interface ChatMessage {
  role: ChatRole;
  content: string | null;
  name: string | null;
  tool_call_id: string | null;
  tool_calls: ToolCall[] | null;
}

// from redel.state
export interface KaniState {
  id: string;
  depth: number;
  parent: string | null;
  children: string[];
  always_included_messages: ChatMessage[];
  chat_history: ChatMessage[];
  state: RunState;
  name: string;
  engine_type: string;
  engine_repr: string;
  functions: AIFunctionState[];
}

export interface AIFunctionState {
  name: string;
  desc: string;
  auto_retry: boolean;
  auto_truncate: number | null;
  after: ChatRole;
  json_schema: object;
}

// from server.models
export interface SessionMeta {
  id: string;
  title: string | null;
  last_modified: number;
  n_events: number;
}

export interface SaveMeta extends SessionMeta {
  grouping_prefix: string[];
}

export interface SessionState extends SessionMeta {
  state: KaniState[];
}

// ===== kanpai events =====
export interface BaseEvent {
  type: string;
}

// ---- server events ----
export interface WSError extends BaseEvent {
  msg: string;
}

export interface KaniSpawn extends BaseEvent, KaniState {}

export interface KaniStateChange extends BaseEvent {
  id: string;
  state: RunState;
}

export interface KaniMessage extends BaseEvent {
  id: string;
  msg: ChatMessage;
}

export interface RootMessage extends BaseEvent {
  msg: ChatMessage;
}

export interface StreamDelta extends BaseEvent {
  id: string;
  delta: string;
  role: ChatRole;
}

// ---- client events ----
export interface SendMessage extends BaseEvent {
  type: "send_message";
  content: string;
}
