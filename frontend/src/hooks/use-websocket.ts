"use client";

import { useState, useCallback, useRef, useEffect } from "react";

export type WebSocketStatus = "connecting" | "connected" | "disconnected" | "reconnecting";

interface UseWebSocketOptions {
  url: string;
  onMessage: (data: any) => void;
  onError?: (error: Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectMaxAttempts?: number;
  reconnectBaseDelay?: number;
  heartbeatInterval?: number;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    url,
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    reconnectMaxAttempts = 5,
    reconnectBaseDelay = 1000,
    heartbeatInterval = 30000,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isReconnectingRef = useRef(false);
  const shouldReconnectRef = useRef(true);

  const clearHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    clearHeartbeat();
    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval, clearHeartbeat]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    setStatus("connecting");
    shouldReconnectRef.current = true;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        setReconnectAttempt(0);
        isReconnectingRef.current = false;
        startHeartbeat();
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Ignore ping/pong
          if (data.type === "ping" || data.type === "pong") return;
          onMessage(data);
        } catch {
          // If not JSON, pass raw
          onMessage(event.data);
        }
      };

      ws.onerror = (event) => {
        onError?.(new Error("WebSocket error"));
      };

      ws.onclose = () => {
        setStatus("disconnected");
        clearHeartbeat();
        onDisconnect?.();

        // Attempt reconnection if allowed
        if (shouldReconnectRef.current && !isReconnectingRef.current) {
          const attempt = reconnectAttempt + 1;
          if (attempt <= reconnectMaxAttempts) {
            isReconnectingRef.current = true;
            setStatus("reconnecting");
            setReconnectAttempt(attempt);

            // Exponential backoff with jitter
            const delay = Math.min(
              reconnectBaseDelay * Math.pow(2, attempt - 1) + Math.random() * 1000,
              30000
            );

            reconnectTimeoutRef.current = setTimeout(() => {
              isReconnectingRef.current = false;
              connect();
            }, delay);
          } else {
            setStatus("disconnected");
            setReconnectAttempt(0);
          }
        }
      };
    } catch (err) {
      setStatus("disconnected");
      onError?.(err instanceof Error ? err : new Error("Failed to create WebSocket"));
    }
  }, [url, onMessage, onError, onConnect, onDisconnect, reconnectMaxAttempts, reconnectBaseDelay, reconnectAttempt, startHeartbeat, clearHeartbeat]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    clearHeartbeat();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus("disconnected");
    setReconnectAttempt(0);
  }, [clearHeartbeat]);

  const send = useCallback(
    (data: any) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(typeof data === "string" ? data : JSON.stringify(data));
        return true;
      }
      return false;
    },
    []
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    reconnectAttempt,
    isConnected: status === "connected",
    isReconnecting: status === "reconnecting",
    connect,
    disconnect,
    send,
  };
}
