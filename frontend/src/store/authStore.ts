import { create } from "zustand";
import { clearTokens, storeTokens } from "@/api/client";
import { authApi, User } from "@/api/auth";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!sessionStorage.getItem("access_token"),

  login: async (email, password) => {
    const data = await authApi.login({ email, password });
    storeTokens(data.access_token, data.refresh_token);
    set({ user: data.user, isAuthenticated: true });
  },

  register: async (email, username, password) => {
    const data = await authApi.register({ email, username, password });
    storeTokens(data.access_token, data.refresh_token);
    set({ user: data.user, isAuthenticated: true });
  },

  logout: async () => {
    const refresh = localStorage.getItem("refresh_token") || "";
    if (refresh) await authApi.logout(refresh).catch(() => {});
    clearTokens();
    set({ user: null, isAuthenticated: false });
  },

  loadUser: async () => {
    try {
      const user = await authApi.me();
      set({ user, isAuthenticated: true });
    } catch {
      clearTokens();
      set({ user: null, isAuthenticated: false });
    }
  },
}));
