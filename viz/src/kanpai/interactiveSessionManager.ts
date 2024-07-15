import { API } from "@/kanpai/api";
import type { SessionMeta } from "@/kanpai/models";

/**
 * Global static class to handle the drawer list of interactive sessions.
 */
export class InteractiveSessions {
  public sessions: SessionMeta[] = [];

  public async update() {
    this.sessions = await API.listStatesInteractive();
  }
}
