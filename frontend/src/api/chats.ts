import client from "./client";

export interface Chat {
  id: string;
  title: string;
  system_prompt: string | null;
  is_pinned: boolean;
  is_archived: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
  last_message_preview: string | null;
  message_count: number;
}

export interface ChatListResponse {
  items: Chat[];
  total: number;
  cursor: string | null;
}

export const chatsApi = {
  list: (params?: { search?: string; limit?: number; cursor?: string; include_archived?: boolean }) =>
    client.get<ChatListResponse>("/chats/", { params }).then((r) => r.data),

  create: (data: { title?: string; system_prompt?: string }) =>
    client.post<Chat>("/chats/", data).then((r) => r.data),

  get: (chatId: string) =>
    client.get<Chat>(`/chats/${chatId}`).then((r) => r.data),

  update: (chatId: string, data: { title?: string; system_prompt?: string }) =>
    client.put<Chat>(`/chats/${chatId}`, data).then((r) => r.data),

  delete: (chatId: string) => client.delete(`/chats/${chatId}`),

  pin: (chatId: string) => client.post<Chat>(`/chats/${chatId}/pin`).then((r) => r.data),
  unpin: (chatId: string) => client.post<Chat>(`/chats/${chatId}/unpin`).then((r) => r.data),
  archive: (chatId: string) => client.post<Chat>(`/chats/${chatId}/archive`).then((r) => r.data),
  unarchive: (chatId: string) => client.post<Chat>(`/chats/${chatId}/unarchive`).then((r) => r.data),
};
