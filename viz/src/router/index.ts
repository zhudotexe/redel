import Home from "@/views/Home.vue";
import NotFound from "@/views/NotFound.vue";
import { nextTick } from "vue";
import { createRouter, createWebHistory } from "vue-router";

const DEFAULT_TITLE = "viz";

const routes = [
  { path: "/", name: "Home", component: Home },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: NotFound,
    meta: { title: "404" },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.afterEach((to) => {
  nextTick(() => {
    document.title = (to.meta.title as string) || DEFAULT_TITLE;
  });
});

export default router;
