import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatsApi, Chat } from "@/api/chats";
import { useChatStore } from "@/store/chatStore";

export default function ChatList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { activeChatId, setActiveChat } = useChatStore();
  const [search, setSearch] = useState("");
  const [contextMenu, setContextMenu] = useState<{ chatId: string; x: number; y: number } | null>(null);

  const { data } = useQuery({
    queryKey: ["chats", search],
    queryFn: () => chatsApi.list({ search: search || undefined, limit: 50 }),
  });

  const createMutation = useMutation({
    mutationFn: () => chatsApi.create({ title: "New Chat" }),
    onSuccess: (chat) => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      setActiveChat(chat);
      navigate(`/chat/${chat.id}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (chatId: string) => chatsApi.delete(chatId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["chats"] }),
  });

  const pinMutation = useMutation({
    mutationFn: ({ chatId, pinned }: { chatId: string; pinned: boolean }) =>
      pinned ? chatsApi.pin(chatId) : chatsApi.unpin(chatId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["chats"] }),
  });

  const handleChatClick = (chat: Chat) => {
    setActiveChat(chat);
    navigate(`/chat/${chat.id}`);
  };

  const handleContextMenu = (e: React.MouseEvent, chatId: string) => {
    e.preventDefault();
    setContextMenu({ chatId, x: e.clientX, y: e.clientY });
  };

  const closeContextMenu = () => setContextMenu(null);

  return (
    <div className="flex flex-col h-full" onClick={closeContextMenu}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => createMutation.mutate()}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg transition"
        >
          + New Chat
        </button>
        <input
          type="text"
          placeholder="Search chats…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mt-2 w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto">
        {data?.items.map((chat) => (
          <div
            key={chat.id}
            onContextMenu={(e) => handleContextMenu(e, chat.id)}
            onClick={() => handleChatClick(chat)}
            className={`px-3 py-2.5 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-800 ${
              activeChatId === chat.id ? "bg-blue-50 dark:bg-gray-700" : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {chat.is_pinned && "📌 "}
                {chat.title}
              </span>
              <span className="text-xs text-gray-400 ml-2 shrink-0">
                {new Date(chat.updated_at.endsWith("Z") ? chat.updated_at : chat.updated_at + "Z").toLocaleDateString()}
              </span>
            </div>
            {chat.last_message_preview && (
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                {chat.last_message_preview}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Context menu */}
      {contextMenu && (
        <div
          className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 min-w-32"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
            onClick={() => {
              const chat = data?.items.find((c) => c.id === contextMenu.chatId);
              if (chat) pinMutation.mutate({ chatId: chat.id, pinned: !chat.is_pinned });
              closeContextMenu();
            }}
          >
            {data?.items.find((c) => c.id === contextMenu.chatId)?.is_pinned ? "Unpin" : "Pin"}
          </button>
          <button
            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700"
            onClick={() => {
              deleteMutation.mutate(contextMenu.chatId);
              closeContextMenu();
            }}
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}
