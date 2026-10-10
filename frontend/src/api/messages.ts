import client from "./client";

export interface Message {
  id: string;
  chat_id: string;
  user_id: string | null;
  role: "user" | "assistant" | "system";
  content: string;
  model_used: string | null;
  token_count: number | null;
  created_at: string;
}

export interface MessageListResponse {
  items: Message[];
  cursor: string | null;
  has_more: boolean;
}

export const messagesApi = {
  list: (chatId: string, params?: { limit?: number; cursor?: string }) =>
    client.get<MessageListResponse>(`/chats/${chatId}/messages/`, { params }).then((r) => r.data),

  create: (chatId: string, data: { content: string; role?: string }) =>
    client.post<Message>(`/chats/${chatId}/messages/`, data).then((r) => r.data),

  delete: (chatId: string, messageId: string) =>
    client.delete(`/chats/${chatId}/messages/${messageId}`),

  search: (chatId: string, q: string) =>
    client.get<MessageListResponse>(`/chats/${chatId}/messages/search`, { params: { q } }).then((r) => r.data),
};
