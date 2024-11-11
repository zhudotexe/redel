import {
  type BaseEvent,
  type ChatMessage,
  ChatRole,
  type KaniMessage,
  type KaniSpawn,
  type KaniState,
  type KaniStateChange,
  type RootMessage,
  RunState,
  type SessionMeta,
  type SessionMetaUpdate,
  type SessionState,
  type StreamDelta,
} from "@/redel/models";

export class ReDelState {
  rootMessages: ChatMessage[] = [];
  rootKani?: KaniState;
  meta?: SessionMeta;
  kaniMap: Map<string, KaniState> = new Map<string, KaniState>();
  streamMap: Map<string, string> = new Map<string, string>();

  constructor(state?: SessionState) {
    if (state) {
      this.loadSessionState(state);
    }
  }

  public loadSessionState(data: SessionState) {
    this.kaniMap.clear();
    this.meta = data;
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

  // ==== event handlers - forward ====
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
      case "session_meta_update":
        this.onSessionMetaUpdate(data as SessionMetaUpdate);
        break;
      default:
        console.debug("Unknown event:", data);
    }
  }

  onKaniSpawn(data: KaniSpawn) {
    this.kaniMap.set(data.id, data);
    // set up the root iff it's null
    if (data.parent === null) {
      if (!this.rootKani) {
        this.rootKani = data;
        this.rootMessages = [...data.chat_history];
      }
      return;
    }
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

  onSessionMetaUpdate(data: SessionMetaUpdate) {
    if (!this.meta) {
      console.warn("Got SessionMetaUpdate but session meta is undefined!");
      return;
    }
    this.meta.title = data.title;
  }

  // ==== event handlers - backward ====
  public undoEvent(data: BaseEvent) {
    switch (data.type) {
      case "kani_spawn":
        this.undoKaniSpawn(data as KaniSpawn);
        break;
      case "kani_state_change":
        this.undoKaniStateChange(data as KaniStateChange);
        break;
      case "kani_message":
        this.undoKaniMessage(data as KaniMessage);
        break;
      case "root_message":
        this.undoRootMessage(data as RootMessage);
        break;
      default:
        console.debug("Unhandled event undo:", data);
    }
  }

  undoKaniSpawn(data: KaniSpawn) {
    if (data.parent) {
      const parent = this.kaniMap.get(data.parent);
      if (parent && parent.children.includes(data.id)) {
        parent.children.splice(parent.children.indexOf(data.id), 1);
      } else {
        console.warn("Undoing kani_spawn event but parent kani does not exist or is missing child!");
      }
    } else {
      // delete the root iff it's null
      if (this.rootKani) {
        this.rootKani = undefined;
        this.rootMessages = [];
      }
    }
    this.kaniMap.delete(data.id);
  }

  undoKaniStateChange(data: KaniStateChange) {
    const kani = this.kaniMap.get(data.id);
    if (!kani) {
      console.warn("Undoing kani_state_change event for nonexistent kani!");
      return;
    }
    // this is a best-effort guess since we don't actually know the previous state
    switch (data.state) {
      case RunState.running:
        kani.state = RunState.waiting;
        break;
      case RunState.waiting:
      case RunState.stopped:
        kani.state = RunState.running;
        break;
      default:
        kani.state = RunState.stopped;
    }
  }

  undoKaniMessage(data: KaniMessage) {
    const kani = this.kaniMap.get(data.id);
    if (!kani) {
      console.warn("Undoing kani_message event for nonexistent kani!");
      return;
    }
    // just delete the last one with a sanity check
    const removed = kani.chat_history.pop();
    if (removed?.content !== data.msg.content) {
      console.warn("undoKaniMessage popped an incorrect message!", removed, data.msg);
    }
    // also reset the stream buffer for that kani
    this.streamMap.delete(data.id);
  }

  undoRootMessage(data: RootMessage) {
    const removed = this.rootMessages.pop();
    if (removed?.content !== data.msg.content) {
      console.warn("undoRootMessage popped an incorrect message!", removed, data.msg);
    }
  }
}
