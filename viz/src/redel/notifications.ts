import { reactive } from "vue";

export enum NotificationLevel {
  info,
  success,
  warning,
  danger,
}

export interface Notification {
  level: NotificationLevel;
  message: string;
}

export class Notifications {
  public static notifs: Notification[] = reactive([]);

  public static dismiss(notif: Notification) {
    const idx = this.notifs.indexOf(notif);
    if (idx === -1) return;
    this.notifs.splice(idx, 1);
  }

  // add notifications
  public static info(message: string) {
    console.info(message);
    this.notifs.push({ level: NotificationLevel.info, message });
  }

  public static success(message: string) {
    console.log(message);
    this.notifs.push({ level: NotificationLevel.success, message });
  }

  public static warning(message: string) {
    console.warn(message);
    this.notifs.push({ level: NotificationLevel.warning, message });
  }

  public static error(message: string) {
    console.error(message);
    this.notifs.push({ level: NotificationLevel.danger, message });
  }

  // special handlers
  public static httpError(error: any) {
    console.error(error);
    if (error.response) {
      this.error(`${error.response.status}: ${error.response.data.detail ?? error.response.data.toString()}`);
    } else if (error.request) {
      this.error("Request failed - maybe the server is down?");
    } else {
      this.error(`Unknown internal error: ${error.message}`);
    }
  }
}
