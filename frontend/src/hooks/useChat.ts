import { useState, useCallback, useRef, useEffect } from 'react';
import type { Message, ChatResponse, MapCommand, ToolCall } from '../types/chat';

interface UserLocation {
  lat: number;
  lng: number;
}

interface UseChatReturn {
  messages: Message[];
  isConnected: boolean;
  isLoading: boolean;
  sendMessage: (content: string, fileContext?: Record<string, unknown>) => void;
  mapCommands: MapCommand[];
  clearMapCommands: () => void;
  userLocation: UserLocation | null;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [mapCommands, setMapCommands] = useState<MapCommand[]>([]);
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const streamingIdRef = useRef<string | null>(null);

  // Capture browser geolocation on mount
  useEffect(() => {
    if (!navigator.geolocation) return;
    const onPos = (pos: GeolocationPosition) => {
      setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
    };
    navigator.geolocation.getCurrentPosition(onPos, () => {}, {
      enableHighAccuracy: true,
      timeout: 10000,
    });
  }, []);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/chat`);

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (event) => {
      const data: ChatResponse = JSON.parse(event.data);

      if (data.type === 'tool_call') {
        // Tool call event from middleware — attach to the current streaming message
        const toolCall: ToolCall = {
          name: data.name!,
          arguments: data.arguments ?? {},
          status: data.status as 'executing' | 'completed',
          result: data.result,
        };

        if (!streamingIdRef.current) {
          // Create a new assistant message for streaming with the tool call
          const id = crypto.randomUUID();
          streamingIdRef.current = id;
          const msg: Message = {
            id,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            tools: [toolCall],
          };
          setMessages((prev) => [...prev, msg]);
        } else {
          const sid = streamingIdRef.current;
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== sid) return m;
              const existing = m.tools ?? [];
              // Update existing tool if same name+args (status change), else add new
              const existingIdx = existing.findIndex(
                (t) => t.name === toolCall.name && t.status === 'executing'
              );
              if (existingIdx >= 0 && toolCall.status === 'completed') {
                const updated = [...existing];
                updated[existingIdx] = toolCall;
                return { ...m, tools: updated };
              }
              return { ...m, tools: [...existing, toolCall] };
            })
          );
        }
      } else if (data.type === 'delta') {
        // Append chunk to the current streaming message
        if (!streamingIdRef.current) {
          // Create a new assistant message for streaming
          const id = crypto.randomUUID();
          streamingIdRef.current = id;
          const msg: Message = {
            id,
            role: 'assistant',
            content: data.text ?? '',
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, msg]);
        } else {
          // Append to existing streaming message
          const sid = streamingIdRef.current;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === sid ? { ...m, content: m.content + (data.text ?? '') } : m
            )
          );
        }
      } else if (data.type === 'done') {
        // Replace streaming message with final cleaned text and fire map commands
        if (streamingIdRef.current) {
          const sid = streamingIdRef.current;
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== sid) return m;
              // Mark all tools as completed
              const completedTools = (m.tools ?? []).map((t) => ({
                ...t,
                status: 'completed' as const,
              }));
              return { ...m, content: data.text ?? m.content, tools: completedTools.length > 0 ? completedTools : undefined };
            })
          );
        }
        streamingIdRef.current = null;
        setIsLoading(false);

        if (data.mapCommands && data.mapCommands.length > 0) {
          setMapCommands(data.mapCommands);
        }
      } else if (data.type === 'error') {
        const errorText = `Error: ${data.text}`;
        if (streamingIdRef.current) {
          // Merge error into the existing streaming message (which may have tools)
          const sid = streamingIdRef.current;
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== sid) return m;
              const completedTools = (m.tools ?? []).map((t) => ({
                ...t,
                status: 'completed' as const,
              }));
              return {
                ...m,
                content: errorText,
                tools: completedTools.length > 0 ? completedTools : undefined,
              };
            })
          );
        } else {
          const errorMessage: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: errorText,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorMessage]);
        }
        streamingIdRef.current = null;
        setIsLoading(false);
      }
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback(
    (content: string, fileContext?: Record<string, unknown>) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      const payload: Record<string, unknown> = { message: content };
      if (fileContext) {
        payload.fileContext = fileContext;
      }
      if (userLocation) {
        payload.userLocation = userLocation;
      }

      wsRef.current.send(JSON.stringify(payload));
    },
    []
  );

  const clearMapCommands = useCallback(() => {
    setMapCommands([]);
  }, []);

  return {
    messages,
    isConnected,
    isLoading,
    sendMessage,
    mapCommands,
    clearMapCommands,
    userLocation,
  };
}
