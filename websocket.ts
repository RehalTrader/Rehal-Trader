"use client";

import { useEffect, useRef, useState } from "react";
import type { SignalOut } from "./api";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/signals";

/**
 * Subscribes to the backend's live signal WebSocket and keeps a rolling list of
 * the most recent signals in state. Reconnects automatically with backoff if the
 * connection drops.
 */
export function useLiveSignals(maxItems = 50) {
  const [signals, setSignals] = useState<SignalOut[]>([]);
  const [connected, setConnected] = useState(false);
  const retryDelay = useRef(1000);

  useEffect(() => {
    let socket: WebSocket;
    let cancelled = false;

    function connect() {
      socket = new WebSocket(WS_URL);

      socket.onopen = () => {
        setConnected(true);
        retryDelay.current = 1000;
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as SignalOut;
          setSignals((prev) => [payload, ...prev].slice(0, maxItems));
        } catch {
          // ignore malformed message
        }
      };

      socket.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          setTimeout(connect, retryDelay.current);
          retryDelay.current = Math.min(retryDelay.current * 2, 30000);
        }
      };

      socket.onerror = () => socket.close();
    }

    connect();
    return () => {
      cancelled = true;
      socket?.close();
    };
  }, [maxItems]);

  return { signals, connected };
}
