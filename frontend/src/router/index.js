import { createRouter, createWebHistory } from "vue-router";
import Tixcraft from "@/views/Tixcraft.vue";
import Home from "@/views/Home.vue";
import Log from "@/views/Log.vue";

const routes = [
  {
    path: "/", // 定義訪問該視圖的 URL 路徑
    name: "Home", // 路由名稱
    component: Home,
  },
  {
    path: "/log", // 定義訪問該視圖的 URL 路徑
    name: "Log", // 路由名稱
    component: Log,
  },
  {
    path: "/tixcraft", // 定義訪問該視圖的 URL 路徑
    name: "Tixcraft", // 路由名稱
    component: Tixcraft,
  },
  // 其他路由...
];

const router = createRouter({
    history: createWebHistory(),
    routes,
  });
  
  
export default router;
