import type { BaseEvent, ChatMessage, RootMessage, SendMessage, SessionState } from "@/kanpai/models";
import { ChatRole } from "@/kanpai/models";
import { ReDelState } from "@/kanpai/state";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/api/ws";

/**
 * API client to handle interactive session with the backend.
 */
export class InteractiveClient {
  state: ReDelState;
  sessionId: string;

  // ws
  ws: WebSocket | null = null;
  isWSConnecting = false;
  isWSDisconnected = false;

  // events
  events = new EventTarget();
  isReady: boolean = false;

  public constructor(sessionId: string, startState?: ReDelState) {
    this.sessionId = sessionId;
    if (startState) {
      this.state = startState;
    } else {
      this.state = new ReDelState();
    }
  }

  // ==== lifecycle ====
  public connect() {
    this.ws?.close(1000);
    this.ws = new WebSocket(`${WS_BASE}/${this.sessionId}`);
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
      const response = await axios.get<SessionState>(`${API_BASE}/states/${this.sessionId}`);
      this.state.loadSessionState(response.data);
      // notify ready
      this.isReady = true;
      this.events.dispatchEvent(new Event("_ready"));
      console.debug(`Loaded ${this.state.kaniMap.size} kani states.`);
      return { success: true };
    } catch (error) {
      console.error("Failed to get session state:", error);
      return { success: false, error };
    }
  }

  public sendMessage(msg: string) {
    const payload: SendMessage = { type: "send_message", content: msg };
    this.ws?.send(JSON.stringify(payload));
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
    let message: BaseEvent;
    try {
      message = JSON.parse(data);
      console.debug("RECV", message);
    } catch (e) {
      console.warn(e);
      return;
    }
    this.state.handleEvent(message);
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
    this.connect();
    setTimeout(() => this.attemptReconnect(attempt + 1, maxAttempts), attempt * 1000 + Math.random() * 1000);
  }
}
