import { useCallback, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useChatStore } from "@/store/chatStore";

const WS_BASE = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/chat`;

export function useWebSocket(chatId: string | null) {
  const ws = useRef<WebSocket | null>(null);
  const chunkBuffer = useRef<string[]>([]);
  const rafRef = useRef<number>(0);
  const queryClient = useQueryClient();
  const { setStreaming, appendStreamChunk, streamingMessageId } = useChatStore();

  // Use refs for callbacks to avoid stale closures in the WS handlers
  const setStreamingRef = useRef(setStreaming);
  const appendChunkRef = useRef(appendStreamChunk);
  const queryClientRef = useRef(queryClient);
  useEffect(() => { setStreamingRef.current = setStreaming; }, [setStreaming]);
  useEffect(() => { appendChunkRef.current = appendStreamChunk; }, [appendStreamChunk]);
  useEffect(() => { queryClientRef.current = queryClient; }, [queryClient]);

  const chatIdRef = useRef(chatId);
  useEffect(() => { chatIdRef.current = chatId; }, [chatId]);

  useEffect(() => {
    if (!chatId) return;
    const token = sessionStorage.getItem("access_token");
    if (!token) return;

    const socket = new WebSocket(`${WS_BASE}/${chatId}?token=${token}`);
    ws.current = socket;

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "chunk") {
          chunkBuffer.current.push(data.delta);
          if (!rafRef.current) {
            rafRef.current = requestAnimationFrame(() => {
              rafRef.current = 0;
              const combined = chunkBuffer.current.join("");
              chunkBuffer.current = [];
              appendChunkRef.current(combined);
            });
          }
        } else if (data.type === "done") {
          cancelAnimationFrame(rafRef.current);
          rafRef.current = 0;
          const remaining = chunkBuffer.current.join("");
          if (remaining) appendChunkRef.current(remaining);
          chunkBuffer.current = [];
          setStreamingRef.current(null);
          queryClientRef.current.invalidateQueries({ queryKey: ["messages", chatIdRef.current] });
          queryClientRef.current.invalidateQueries({ queryKey: ["chats"] });
        } else if (data.type === "error") {
          setStreamingRef.current(null);
          console.error("WS error:", data.detail);
        }
      } catch {}
    };

    socket.onclose = () => {
      setStreamingRef.current(null);
    };

    return () => {
      socket.close();
      if (ws.current === socket) ws.current = null;
    };
  }, [chatId]);

  const sendMessage = useCallback(
    (content: string, model: string) => {
      const doSend = (socket: WebSocket) => {
        const tempId = `streaming-${Date.now()}`;
        setStreaming(tempId, "");
        socket.send(JSON.stringify({ type: "message", content, model }));
      };

      const current = ws.current;
      if (current && current.readyState === WebSocket.OPEN) {
        doSend(current);
        return;
      }

      // WS not ready — create a fresh connection for this send
      const token = sessionStorage.getItem("access_token");
      if (!chatId || !token) return;
      const socket = new WebSocket(`${WS_BASE}/${chatId}?token=${token}`);
      ws.current = socket;

      // Set up message handler on this new socket too
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "chunk") {
            chunkBuffer.current.push(data.delta);
            if (!rafRef.current) {
              rafRef.current = requestAnimationFrame(() => {
                rafRef.current = 0;
                const combined = chunkBuffer.current.join("");
                chunkBuffer.current = [];
                appendChunkRef.current(combined);
              });
            }
          } else if (data.type === "done") {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = 0;
            const remaining = chunkBuffer.current.join("");
            if (remaining) appendChunkRef.current(remaining);
            chunkBuffer.current = [];
            setStreamingRef.current(null);
            queryClientRef.current.invalidateQueries({ queryKey: ["messages", chatIdRef.current] });
            queryClientRef.current.invalidateQueries({ queryKey: ["chats"] });
          } else if (data.type === "error") {
            setStreamingRef.current(null);
          }
        } catch {}
      };
      socket.onclose = () => setStreamingRef.current(null);

      socket.addEventListener("open", () => doSend(socket), { once: true });
    },
    [chatId, setStreaming]
  );

  const stopGeneration = useCallback(() => {
    ws.current?.send(JSON.stringify({ type: "stop" }));
    setStreaming(null);
  }, [setStreaming]);

  return { sendMessage, stopGeneration, isStreaming: !!streamingMessageId };
}
