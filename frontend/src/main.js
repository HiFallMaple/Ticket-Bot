import { createApp } from "vue";
import App from "./App.vue";
import router from "./router"; // 引入路由器
import PrimeVue from "primevue/config";
import Aura from "@primevue/themes/aura";
import ToastService from "primevue/toastservice";
import ConfirmationService from "primevue/confirmationservice";
import Ripple from "primevue/ripple";

import "@/assets/fonts/fonts.css";
import "primeflex/primeflex.css"; // 引入 PrimeFlex
import "primeicons/primeicons.css"; // 引入 PrimeIcons
import "primeflex/themes/primeone-light.css";
import "./style.css";

const app = createApp(App);

// 註冊 ripple 指令
app.directive("ripple", Ripple);

// 註冊 PrimeVue
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: "system",
      cssLayer: false,
    },
  },
});

app.use(ConfirmationService);
app.use(ToastService);
app.use(router);

// 挂載應用
app.mount("#app");
