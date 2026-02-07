import { useEffect, useRef, useState } from "react";

type Message = Record<string, unknown>;

export default function useWebSocket(url: string) {
  const socketRef = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, data]);
      } catch {
        setMessages((prev) => [...prev, { raw: event.data }]);
      }
    };

    return () => {
      socket.close();
    };
  }, [url]);

  return { messages, socket: socketRef.current };
}
