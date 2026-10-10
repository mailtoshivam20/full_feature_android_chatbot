import { useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import { messagesApi, Message } from "@/api/messages";
import { useQueryClient } from "@tanstack/react-query";
import "highlight.js/styles/github-dark.css";

interface Props {
  message: Message;
  chatId: string;
  onRegenerate?: () => void;
}

export default function MessageBubble({ message, chatId, onRegenerate }: Props) {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDelete = async () => {
    if (!confirm("Delete this message?")) return;
    await messagesApi.delete(chatId, message.id);
    queryClient.invalidateQueries({ queryKey: ["messages", chatId] });
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4 group`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm relative ${
          isUser
            ? "bg-blue-600 text-white rounded-br-sm"
            : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-bl-sm shadow-sm"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown rehypePlugins={[rehypeHighlight]}>{message.content}</ReactMarkdown>
          </div>
        )}

        {/* Action bar */}
        <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-xs opacity-50">
            {new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
          <button
            onClick={handleCopy}
            className="text-xs opacity-60 hover:opacity-100 ml-auto"
            title="Copy"
          >
            {copied ? "✓" : "⎘"}
          </button>
          <button
            onClick={handleDelete}
            className="text-xs opacity-60 hover:opacity-100 text-red-400"
            title="Delete"
          >
            ×
          </button>
          {!isUser && onRegenerate && (
            <button
              onClick={onRegenerate}
              className="text-xs opacity-60 hover:opacity-100"
              title="Regenerate"
            >
              ↺
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
