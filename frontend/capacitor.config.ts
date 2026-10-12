import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.chatapp.android",
  appName: "ChatApp",
  webDir: "dist",
  android: {
    allowMixedContent: true,
  },
  server: {
    // During development with live reload, point to your PC's IP:
    // url: "http://192.168.1.x:5173",
    // cleartext: true,
  },
};

export default config;
