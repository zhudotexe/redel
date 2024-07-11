import type {
  BaseEvent,
  ChatMessage,
  KaniMessage,
  KaniSpawn,
  KaniState,
  KaniStateChange,
  RootMessage,
  SessionState,
  StreamDelta,
} from "@/kanpai/models";
import { ChatRole } from "@/kanpai/models";

export class ReDelState {
  rootMessages: ChatMessage[] = [];
  rootKani?: KaniState;
  kaniMap: Map<string, KaniState> = new Map<string, KaniState>();
  streamMap: Map<string, string> = new Map<string, string>();

  constructor(state?: SessionState) {
    if (state) {
      this.loadSessionState(state);
    }
  }

  public loadSessionState(data: SessionState) {
    this.kaniMap.clear();
    // hydrate the app state
    for (const kani of data.state) {
      this.kaniMap.set(kani.id, kani);
      // also set up the root chat state
      if (kani.parent === null) {
        this.rootKani = kani;
        // ensure it is a copy
        this.rootMessages = [...kani.chat_history];
      }
    }
  }

  // ==== event handlers ====
  public handleEvent(data: BaseEvent) {
    switch (data.type) {
      case "kani_spawn":
        this.onKaniSpawn(data as KaniSpawn);
        break;
      case "kani_state_change":
        this.onKaniStateChange(data as KaniStateChange);
        break;
      case "kani_message":
        this.onKaniMessage(data as KaniMessage);
        break;
      case "root_message":
        this.onRootMessage(data as RootMessage);
        break;
      case "stream_delta":
        this.onStreamDelta(data as StreamDelta);
        break;
      default:
        console.warn("Unknown event:", data);
    }
  }

  onKaniSpawn(data: KaniSpawn) {
    this.kaniMap.set(data.id, data);
    if (data.parent === null) return;
    const parent = this.kaniMap.get(data.parent);
    if (!parent) {
      console.warn("Got kani_spawn event but parent kani does not exist!");
      return;
    }
    if (parent.children.includes(data.id)) return;
    parent.children.push(data.id);
  }

  onKaniStateChange(data: KaniStateChange) {
    const kani = this.kaniMap.get(data.id);
    if (!kani) {
      console.warn("Got kani_state_change event for nonexistent kani!");
      return;
    }
    kani.state = data.state;
  }

  onKaniMessage(data: KaniMessage) {
    const kani = this.kaniMap.get(data.id);
    if (!kani) {
      console.warn("Got kani_message event for nonexistent kani!");
      return;
    }
    kani.chat_history.push(data.msg);
    // also reset the stream buffer for that kani
    this.streamMap.delete(data.id);
  }

  onRootMessage(data: RootMessage) {
    this.rootMessages.push(data.msg);
  }

  onStreamDelta(data: StreamDelta) {
    // only for assistant messages
    if (data.role != ChatRole.assistant) return;
    const buf = this.streamMap.get(data.id);
    if (!buf) {
      this.streamMap.set(data.id, data.delta);
      return;
    }
    this.streamMap.set(data.id, buf + data.delta);
  }
}
