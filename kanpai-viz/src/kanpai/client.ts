import type { ChatMessage, KaniMessage, KaniSpawn, RootMessage, SendMessage, WSMessage } from "@/kanpai/models";
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
  kaniMap: Map<string, KaniState> = new Map<string, KaniState>();

  // waiters
  rootMessageWaiterResolvers: ((msg: ChatMessage) => void)[] = [];

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
      // hydrate the app state
      for (const kani of response.data.kanis) {
        this.kaniMap.set(kani.id, kani);
        // also set up the root chat state
        if (kani.parent === null) {
          // ensure it is a copy
          this.rootMessages = [...kani.chat_history];
        }
      }
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
  }

  onKaniMessage(data: KaniMessage) {
    const kani = this.kaniMap.get(data.id);
    if (!kani) {
      console.warn("Got kani_message event for nonexistant message!");
      return;
    }
    kani.chat_history.push(data.msg);
  }

  onRootMessage(data: RootMessage) {
    this.rootMessages.push(data.msg);
    if (data.msg.role == ChatRole.assistant && data.msg.function_call === null) {
      this.rootMessageWaiterResolvers.forEach((resolve) => resolve(data.msg));
      this.rootMessageWaiterResolvers = [];
    }
  }

  // ==== utils ====
  public async waitForFullReply() {
    return new Promise<ChatMessage>((resolve) => {
      this.rootMessageWaiterResolvers.push(resolve);
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
      case "kani_message":
        this.onKaniMessage(message as KaniMessage);
        break;
      case "root_message":
        this.onRootMessage(message as RootMessage);
        break;
      default:
        console.warn("Unknown websocket event:", message);
    }
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
