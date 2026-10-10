import { useParams, Link } from "react-router-dom";
import { useUIStore } from "@/store/uiStore";
import ChatList from "@/components/ChatList";
import ChatWindow from "@/components/ChatWindow";
import ModelSelector from "@/components/ModelSelector";
import { useAuthStore } from "@/store/authStore";
import client from "@/api/client";

export default function ChatPage() {
  const { chatId } = useParams<{ chatId?: string }>();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { user } = useAuthStore();

  const handleExport = async (format: "json" | "pdf") => {
    if (!chatId) return;
    const res = await client.get(`/chats/${chatId}/export`, {
      params: { format },
      responseType: "blob",
    });
    const url = URL.createObjectURL(new Blob([res.data]));
    const a = document.createElement("a");
    a.href = url;
    a.download = `chat.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-72" : "w-0"
        } shrink-0 transition-all duration-200 overflow-hidden border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex flex-col`}
      >
        <ChatList />
        {/* Sidebar footer */}
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 flex items-center gap-2">
          <Link
            to="/profile"
            className="text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white truncate flex-1"
          >
            👤 {user?.username}
          </Link>
          <Link
            to="/settings"
            className="text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white"
            title="Settings"
          >
            ⚙️
          </Link>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-12 shrink-0 border-b border-gray-200 dark:border-gray-700 flex items-center px-3 gap-3 bg-white dark:bg-gray-900">
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 shrink-0"
            aria-label="Toggle sidebar"
          >
            ☰
          </button>

          <span className="text-sm text-gray-500 dark:text-gray-400 truncate flex-1">
            {chatId ? "Chat" : "Select or create a chat"}
          </span>

          <div className="flex items-center gap-2 shrink-0">
            <ModelSelector />
            {chatId && (
              <div className="relative group">
                <button className="text-xs px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500">
                  Export ▾
                </button>
                <div className="absolute right-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 hidden group-hover:block z-10">
                  <button
                    onClick={() => handleExport("json")}
                    className="block w-full text-left px-4 py-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Export JSON
                  </button>
                  <button
                    onClick={() => handleExport("pdf")}
                    className="block w-full text-left px-4 py-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Export PDF
                  </button>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Chat content */}
        {chatId ? (
          <ChatWindow chatId={chatId} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Select a chat from the sidebar or create a new one.
          </div>
        )}
      </div>
    </div>
  );
}
