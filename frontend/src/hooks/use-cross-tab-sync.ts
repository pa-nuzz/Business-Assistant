'use client';

import { useEffect, useCallback, useRef } from 'react';

interface SyncMessage {
  type: 'conversation_created' | 'conversation_deleted' | 'conversation_updated' | 'chat_state_cleared' | 'auth_change' | 'force_refresh';
  payload?: any;
  timestamp: number;
  sourceTab: string;
}

const TAB_ID = Math.random().toString(36).substring(2, 9);
const CHANNEL_NAME = 'aeiou-app-sync';

export function useCrossTabSync(
  onMessage: (message: SyncMessage) => void,
  options: { enabled?: boolean } = {}
) {
  const { enabled = true } = options;
  const channelRef = useRef<BroadcastChannel | null>(null);
  const onMessageRef = useRef(onMessage);

  // Keep callback reference up to date
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  // Initialize BroadcastChannel
  useEffect(() => {
    if (!enabled || typeof window === 'undefined') return;

    // Create BroadcastChannel for cross-tab communication
    const channel = new BroadcastChannel(CHANNEL_NAME);
    channelRef.current = channel;

    // Listen for messages from other tabs
    const handleMessage = (event: MessageEvent<SyncMessage>) => {
      const message = event.data;
      
      // Ignore messages from this tab
      if (message.sourceTab === TAB_ID) return;
      
      // Check if message is recent (within last 5 seconds)
      if (Date.now() - message.timestamp > 5000) return;
      
      onMessageRef.current(message);
    };

    channel.addEventListener('message', handleMessage);

    // Also listen for storage events (fallback for older browsers)
    const handleStorage = (e: StorageEvent) => {
      if (e.key === CHANNEL_NAME && e.newValue) {
        try {
          const message: SyncMessage = JSON.parse(e.newValue);
          if (message.sourceTab !== TAB_ID && Date.now() - message.timestamp < 5000) {
            onMessageRef.current(message);
          }
        } catch {
          // Ignore invalid messages
        }
      }
    };

    window.addEventListener('storage', handleStorage);

    return () => {
      channel.removeEventListener('message', handleMessage);
      channel.close();
      window.removeEventListener('storage', handleStorage);
    };
  }, [enabled]);

  // Send message to other tabs
  const broadcast = useCallback((type: SyncMessage['type'], payload?: any) => {
    if (typeof window === 'undefined') return;

    const message: SyncMessage = {
      type,
      payload,
      timestamp: Date.now(),
      sourceTab: TAB_ID,
    };

    // Send via BroadcastChannel (modern browsers)
    if (channelRef.current) {
      channelRef.current.postMessage(message);
    }

    // Fallback: use localStorage for broader compatibility
    try {
      localStorage.setItem(CHANNEL_NAME, JSON.stringify(message));
      // Clean up after a short delay
      setTimeout(() => localStorage.removeItem(CHANNEL_NAME), 100);
    } catch {
      // Ignore storage errors
    }
  }, []);

  return { broadcast, tabId: TAB_ID };
}

// Convenience hooks for specific sync actions
export function useConversationSync(onRefresh: () => void) {
  const { broadcast } = useCrossTabSync((message) => {
    if (
      message.type === 'conversation_created' ||
      message.type === 'conversation_deleted' ||
      message.type === 'conversation_updated' ||
      message.type === 'force_refresh'
    ) {
      onRefresh();
    }
  });

  const notifyConversationCreated = useCallback(() => {
    broadcast('conversation_created');
  }, [broadcast]);

  const notifyConversationDeleted = useCallback(() => {
    broadcast('conversation_deleted');
  }, [broadcast]);

  const notifyConversationUpdated = useCallback(() => {
    broadcast('conversation_updated');
  }, [broadcast]);

  return {
    notifyConversationCreated,
    notifyConversationDeleted,
    notifyConversationUpdated,
  };
}

export function useChatSync(onClear: () => void) {
  const { broadcast } = useCrossTabSync((message) => {
    if (message.type === 'chat_state_cleared') {
      onClear();
    }
  });

  const notifyChatCleared = useCallback(() => {
    broadcast('chat_state_cleared');
  }, [broadcast]);

  return { notifyChatCleared };
}

export function useAuthSync(onAuthChange: () => void) {
  const { broadcast } = useCrossTabSync((message) => {
    if (message.type === 'auth_change') {
      onAuthChange();
    }
  });

  const notifyAuthChange = useCallback((action: 'login' | 'logout') => {
    broadcast('auth_change', { action });
  }, [broadcast]);

  return { notifyAuthChange };
}
