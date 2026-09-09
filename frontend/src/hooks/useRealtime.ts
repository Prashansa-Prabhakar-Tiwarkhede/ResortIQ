import { useEffect, useRef } from "react";

const WS_BASE = (import.meta as any).env?.VITE_WS_BASE || "ws://localhost:8000/ws";

export function useRealtime(onMessage: (msg: any) => void) {
  const cbRef = useRef(onMessage);
  cbRef.current = onMessage;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(WS_BASE);
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          cbRef.current(data);
        } catch {
          // ignore malformed messages
        }
      };
      ws.onclose = () => {
        if (!cancelled) retryTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
      ws?.close();
    };
  }, []);
}
