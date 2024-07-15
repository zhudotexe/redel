import "@/global.scss";
import { InteractiveSessions } from "@/kanpai/interactiveSessionManager";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faGithub } from "@fortawesome/free-brands-svg-icons";
import {
  faArrowUpRightFromSquare,
  faBookOpen,
  faCalendarDay,
  faCirclePlus,
  faDiagramProject,
  faFile,
  faFolderOpen,
  faHashtag,
  faSearch,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

import { createApp, reactive } from "vue";
import App from "./App.vue";
import router from "./router";

// ==== fontawesome ====
// brands
library.add(faGithub);
// regular
library.add(
  faBookOpen,
  faArrowUpRightFromSquare,
  faFolderOpen,
  faDiagramProject,
  faSearch,
  faCalendarDay,
  faHashtag,
  faFile,
  faCirclePlus,
);

// ==== init ====
const app = createApp(App)
  .use(router)
  .component("font-awesome-icon", FontAwesomeIcon)
  .provide<InteractiveSessions>("interactiveSessionManager", reactive(new InteractiveSessions()));

app.mount("#app");
