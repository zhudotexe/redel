import type { SessionState } from "@/kanpai/models";
import { Notifications } from "@/kanpai/notifications";
import axios from "axios";

export const API_BASE = "http://127.0.0.1:8000/api";
export const WS_BASE = "ws://127.0.0.1:8000/api/ws";

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
  public static async createStateInteractive(startContent?: string) {
    const data = startContent ? { start_content: startContent } : undefined;
    const response = await axios.post<SessionState>(`${API_BASE}/states`, data);
    return response.data;
  }
}
