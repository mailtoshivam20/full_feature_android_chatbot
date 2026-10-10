import client from "./client";

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export const authApi = {
  register: (data: { email: string; username: string; password: string }) =>
    client.post<TokenResponse>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    client.post<TokenResponse>("/auth/login", data).then((r) => r.data),

  logout: (refresh_token: string) =>
    client.post("/auth/logout", { refresh_token }),

  me: () => client.get<User>("/auth/me").then((r) => r.data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    client.put("/auth/me/password", data),
};
