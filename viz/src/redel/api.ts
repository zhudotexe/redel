import type { BaseEvent, SaveMeta, SessionState } from "@/redel/models";
import { Notifications } from "@/redel/notifications";
import axios from "axios";

export const API_BASE = "https://redel-demo.zhu.codes/api";
export const WS_BASE = "wss://redel-demo.zhu.codes/api/ws";

// On error, automatically add an error notification to Notifications.
axios.interceptors.request.use(
  // noop on success
  (response) => response,
  function (error) {
    Notifications.error(error.message);
    return Promise.reject(error);
  },
);

axios.interceptors.response.use(
  // noop on success
  (response) => response,
  // send httpError to notifications on error
  function (error) {
    Notifications.httpError(error);
    return Promise.reject(error);
  },
);

/**
 * A simple static class to expose all the ReDel REST endpoints.
 */
export class API {
  ////////// SAVES //////////
  public static async listSaves() {
    const response = await axios.get<SaveMeta[]>(`${API_BASE}/saves`);
    return response.data;
  }

  public static async getSaveState(saveId: string) {
    const response = await axios.get<SessionState>(`${API_BASE}/saves/${saveId}`);
    return response.data;
  }

  public static async getSaveEvents(saveId: string) {
    const response = await axios.get<BaseEvent[]>(`${API_BASE}/saves/${saveId}/events`);
    return response.data;
  }

  public static async deleteSave(saveId: string) {
    const response = await axios.delete<SaveMeta>(`${API_BASE}/saves/${saveId}`);
    return response.data;
  }

  ////////// INTERACTIVE //////////
  public static async listStatesInteractive() {
    const response = await axios.get<SessionState[]>(`${API_BASE}/states`);
    return response.data;
  }

  public static async createStateInteractive(startContent?: string) {
    const data = startContent ? { start_content: startContent } : undefined;
    const response = await axios.post<SessionState>(`${API_BASE}/states`, data);
    return response.data;
  }

  public static async getStateInteractive(sessionId: string) {
    const response = await axios.get<SessionState>(`${API_BASE}/states/${sessionId}`);
    return response.data;
  }
}
