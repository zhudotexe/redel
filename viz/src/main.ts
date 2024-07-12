import "@/global.scss";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faGithub } from "@fortawesome/free-brands-svg-icons";
import { faArrowUpRightFromSquare, faBookOpen, faFolderOpen } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

// ==== fontawesome ====
// brands
library.add(faGithub);
// regular
library.add(faBookOpen, faArrowUpRightFromSquare, faFolderOpen);

// ==== init ====
const app = createApp(App).use(router).component("font-awesome-icon", FontAwesomeIcon);

app.mount("#app");
