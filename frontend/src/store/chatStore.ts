import { create } from "zustand";
import { Chat } from "@/api/chats";
import { Message } from "@/api/messages";

interface ChatState {
  activeChatId: string | null;
  activeChat: Chat | null;
  streamingMessageId: string | null;
  streamingContent: string;
  selectedModel: string;
  setActiveChat: (chat: Chat | null) => void;
  setActiveChatId: (id: string | null) => void;
  setStreaming: (messageId: string | null, content?: string) => void;
  appendStreamChunk: (chunk: string) => void;
  setSelectedModel: (model: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  activeChatId: null,
  activeChat: null,
  streamingMessageId: null,
  streamingContent: "",
  selectedModel: "gpt-4o-mini",

  setActiveChat: (chat) =>
    set({ activeChat: chat, activeChatId: chat?.id ?? null }),

  setActiveChatId: (id) => set({ activeChatId: id }),

  setStreaming: (messageId, content = "") =>
    set({ streamingMessageId: messageId, streamingContent: content }),

  appendStreamChunk: (chunk) =>
    set((state) => ({ streamingContent: state.streamingContent + chunk })),

  setSelectedModel: (model) => set({ selectedModel: model }),
}));
