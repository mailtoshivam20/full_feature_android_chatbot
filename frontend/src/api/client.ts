import axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from "axios";

const client = axios.create({ baseURL: "/api/v1" });

let isRefreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

function getAccessToken(): string {
  try {
    const raw = sessionStorage.getItem("access_token");
    return raw || "";
  } catch {
    return "";
  }
}

function setAccessToken(token: string) {
  try {
    sessionStorage.setItem("access_token", token);
  } catch {}
}

function getRefreshToken(): string {
  try {
    return localStorage.getItem("refresh_token") || "";
  } catch {
    return "";
  }
}

export function storeTokens(access: string, refresh: string) {
  setAccessToken(access);
  try {
    localStorage.setItem("refresh_token", refresh);
  } catch {}
}

export function clearTokens() {
  try {
    sessionStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  } catch {}
}

client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    original._retry = true;
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      window.location.href = "/login";
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve) => {
        refreshQueue.push((token) => {
          original.headers = { ...original.headers, Authorization: `Bearer ${token}` };
          resolve(client(original));
        });
      });
    }

    isRefreshing = true;
    try {
      const res = await axios.post("/api/v1/auth/refresh", { refresh_token: refreshToken });
      const { access_token, refresh_token } = res.data;
      storeTokens(access_token, refresh_token);
      refreshQueue.forEach((cb) => cb(access_token));
      refreshQueue = [];
      original.headers = { ...original.headers, Authorization: `Bearer ${access_token}` };
      return client(original);
    } catch {
      clearTokens();
      window.location.href = "/login";
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  }
);

export default client;
