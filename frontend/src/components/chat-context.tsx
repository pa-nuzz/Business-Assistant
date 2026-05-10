'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  created_at?: string;
  thinkingSteps?: string[];
}

interface ChatContextType {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  inputValue: string;
  setInputValue: (value: string) => void;
  currentConversationId: string | undefined;
  setCurrentConversationId: (id: string | undefined) => void;
  clearState: () => void;
  saveState: () => void;
  loadState: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>();

  // Save state to localStorage
  const saveState = useCallback(() => {
    if (typeof window !== 'undefined') {
      const state = {
        messages,
        inputValue,
        currentConversationId,
        timestamp: Date.now(),
      };
      localStorage.setItem('aeiou-chat-state', JSON.stringify(state));
    }
  }, [messages, inputValue, currentConversationId]);

  // Load state from localStorage
  const loadState = useCallback(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('aeiou-chat-state');
        if (saved) {
          const state = JSON.parse(saved);
          // Only restore if saved less than 24 hours ago
          if (state.timestamp && Date.now() - state.timestamp < 24 * 60 * 60 * 1000) {
            setMessages(state.messages || []);
            setInputValue(state.inputValue || '');
            setCurrentConversationId(state.currentConversationId);
          }
        }
      } catch (error) {
        // Silently fail - localStorage might be disabled or corrupted
        console.warn('Failed to load chat state:', error);
      }
    }
  }, []);

  // Auto-save state when it changes
  useEffect(() => {
    const timeoutId = setTimeout(saveState, 1000); // Debounce saves
    return () => clearTimeout(timeoutId);
  }, [saveState]);

  // Load state on mount
  useEffect(() => {
    loadState();
  }, [loadState]);

  const clearState = useCallback(() => {
    setMessages([]);
    setInputValue('');
    setCurrentConversationId(undefined);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('aeiou-chat-state');
    }
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        inputValue,
        setInputValue,
        currentConversationId,
        setCurrentConversationId,
        clearState,
        saveState,
        loadState,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
