import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { messagesApi, Message } from "@/api/messages";
import { useChatStore } from "@/store/chatStore";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";
import { useWebSocket } from "@/hooks/useWebSocket";

interface Props {
  chatId: string;
}

export default function ChatWindow({ chatId }: Props) {
  const { streamingContent, streamingMessageId, selectedModel } = useChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevScrollHeightRef = useRef(0);
  const [atBottom, setAtBottom] = useState(true);

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ["messages", chatId],
    queryFn: ({ pageParam }) =>
      messagesApi.list(chatId, { limit: 30, cursor: pageParam as string | undefined }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.cursor ?? undefined,
  });

  const messages: Message[] = data?.pages.flatMap((p) => p.items) ?? [];

  const { sendMessage, stopGeneration, isStreaming } = useWebSocket(chatId);

  // Preserve scroll position when loading older messages upward
  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (isFetchingNextPage) {
      prevScrollHeightRef.current = el.scrollHeight;
    } else if (prevScrollHeightRef.current) {
      el.scrollTop = el.scrollHeight - prevScrollHeightRef.current;
      prevScrollHeightRef.current = 0;
    }
  }, [isFetchingNextPage, data]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (atBottom) {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    }
  }, [messages.length, streamingContent, atBottom]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    setAtBottom(nearBottom);
    if (el.scrollTop < 80 && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  const handleSend = (content: string) => {
    sendMessage(content, selectedModel);
  };

  const handleRegenerate = (msg: Message) => {
    const prevUser = [...messages].reverse().find((m) => m.role === "user");
    if (prevUser) sendMessage(prevUser.content, selectedModel);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-4"
      >
        {isFetchingNextPage && (
          <div className="text-center text-xs text-gray-400 mb-2">Loading…</div>
        )}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            chatId={chatId}
            onRegenerate={msg.role === "assistant" ? () => handleRegenerate(msg) : undefined}
          />
        ))}
        {/* Streaming bubble */}
        {isStreaming && streamingContent && (
          <div className="flex justify-start mb-4">
            <div className="max-w-[80%] rounded-2xl rounded-bl-sm px-4 py-3 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
              <p className="text-gray-900 dark:text-white whitespace-pre-wrap">{streamingContent}</p>
              <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-0.5" />
            </div>
          </div>
        )}
        {isStreaming && !streamingContent && (
          <div className="flex justify-start mb-4">
            <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
              <div className="flex gap-1 items-center h-4">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}
      </div>

      <MessageInput
        onSend={handleSend}
        onStop={stopGeneration}
        isStreaming={isStreaming}
      />
    </div>
  );
}
