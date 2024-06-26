import type {
  ChatMessage,
  KaniMessage,
  KaniSpawn,
  KaniStateChange,
  RootMessage,
  SendMessage,
  StreamDelta,
  WSMessage,
} from "@/kanpai/models";
import { ChatRole } from "@/kanpai/models";
import type { AppState, KaniState } from "@/kanpai/state";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/api";
const WS_URL = "ws://127.0.0.1:8000/api/ws";

export class KanpaiClient {
  // ws state
  ws: WebSocket | null = null;
  isWSConnecting = false;
  isWSDisconnected = false;

  // kanis
  rootMessages: ChatMessage[] = [];
  rootKani?: KaniState;
  kaniMap: Map<string, KaniState> = new Map<string, KaniState>();
  streamMap: Map<string, string> = new Map<string, string>();

  // events
  events = new EventTarget();
  isReady: boolean = false;

  // ==== lifecycle ====
  public init() {
    this.ws?.close(1000);
    this.ws = new WebSocket(WS_URL);
    this.isWSConnecting = true;
    this.ws.addEventListener("open", () => this.onWSOpen());
    this.ws.addEventListener("close", (event) => this.onWSClose(event));
    this.ws.addEventListener("error", (event) => console.warn("WebSocket error: ", event));
    this.ws.addEventListener("message", (event) => this.onRawMessage(event.data));
  }

  public close() {
    this.ws?.close(1000);
  }

  // ==== API ====
  public async getState() {
    try {
      this.kaniMap.clear();
      const response = await axios.get<AppState>(`${API_BASE}/state`);
      // const response = { data: testAppState2 }; // todo comment to use real data
      // hydrate the app state
      for (const kani of response.data.kanis) {
        this.kaniMap.set(kani.id, kani);
        // also set up the root chat state
        if (kani.parent === null) {
          this.rootKani = kani;
          // ensure it is a copy
          this.rootMessages = [...kani.chat_history];
        }
      }
      // notify ready
      this.isReady = true;
      this.events.dispatchEvent(new Event("_ready"));
      console.debug(`Loaded ${this.kaniMap.size} kani states.`);
    } catch (error) {
      console.error("Failed to get app state:", error);
    }
  }

  public sendMessage(msg: string) {
    const payload: SendMessage = { type: "send_message", content: msg };
    this.ws?.send(JSON.stringify(payload));
  }

  // ==== ws event handlers ====
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

  // ==== utils ====
  public async waitForReady() {
    if (this.isReady) return true;
    return new Promise<boolean>((resolve) => {
      this.events.addEventListener("_ready", () => resolve(true));
    });
  }

  public async waitForFullReply() {
    return new Promise<ChatMessage>((resolve) => {
      this.events.addEventListener("root_message", ((e: CustomEvent<RootMessage>) => {
        const msg = e.detail.msg;
        if (msg.role == ChatRole.assistant && msg.tool_calls === null) {
          resolve(msg);
        }
      }) as EventListener);
    });
  }

  // ==== event handlers ====
  onRawMessage(data: string) {
    let message: WSMessage;
    try {
      message = JSON.parse(data);
      console.debug("RECV", message);
    } catch (e) {
      console.warn(e);
      return;
    }

    switch (message.type) {
      case "kani_spawn":
        this.onKaniSpawn(message as KaniSpawn);
        break;
      case "kani_state_change":
        this.onKaniStateChange(message as KaniStateChange);
        break;
      case "kani_message":
        this.onKaniMessage(message as KaniMessage);
        break;
      case "root_message":
        this.onRootMessage(message as RootMessage);
        break;
      case "stream_delta":
        this.onStreamDelta(message as StreamDelta);
        break;
      default:
        console.warn("Unknown websocket event:", message);
    }
    this.events.dispatchEvent(new CustomEvent(message.type, { detail: message }));
  }

  onWSOpen() {
    console.log("WS connected");
    this.isWSDisconnected = false;
    this.isWSConnecting = false;
  }

  onWSClose(event: CloseEvent) {
    console.log(`WS closed with ${event.code} (reason=${event.reason}; clean=${event.wasClean})`);
    this.isWSDisconnected = true;
    if (event.wasClean && event.code !== 1012) {
      this.isWSConnecting = false;
    } else if (!this.isWSConnecting) {
      // attempt reconnect with exponential backoff
      this.attemptReconnect(1);
    }
  }

  attemptReconnect(attempt: number, maxAttempts = 5) {
    if (!this.isWSDisconnected) return;
    if (attempt > maxAttempts) {
      this.isWSDisconnected = true;
      this.isWSConnecting = false;
      return;
    }
    console.log(`Attempting to reconnect (try ${attempt} of ${maxAttempts})...`);
    this.init();
    setTimeout(() => this.attemptReconnect(attempt + 1, maxAttempts), attempt * 1000 + Math.random() * 1000);
  }
}
