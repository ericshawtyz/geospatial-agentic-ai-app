import { useState, useCallback, useRef } from 'react';

export type NotificationSeverity = 'info' | 'success' | 'error';

export interface Notification {
  id: number;
  message: string;
  severity: NotificationSeverity;
}

let nextId = 1;

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const timers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: number) => {
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const notify = useCallback(
    (message: string, severity: NotificationSeverity = 'info', durationMs = 4000) => {
      const id = nextId++;
      setNotifications((prev) => [...prev, { id, message, severity }]);

      if (durationMs > 0) {
        const timer = setTimeout(() => {
          timers.current.delete(id);
          setNotifications((prev) => prev.filter((n) => n.id !== id));
        }, durationMs);
        timers.current.set(id, timer);
      }

      return id;
    },
    []
  );

  const update = useCallback(
    (id: number, message: string, severity: NotificationSeverity, durationMs = 4000) => {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, message, severity } : n))
      );

      // Reset auto-dismiss timer
      const oldTimer = timers.current.get(id);
      if (oldTimer) clearTimeout(oldTimer);

      if (durationMs > 0) {
        const timer = setTimeout(() => {
          timers.current.delete(id);
          setNotifications((prev) => prev.filter((n) => n.id !== id));
        }, durationMs);
        timers.current.set(id, timer);
      }
    },
    []
  );

  return { notifications, notify, update, dismiss };
}
