'use client';

import React, { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from 'react';
import { usePathname } from 'next/navigation';

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  created_at?: string;
}

interface ChatState {
  messages: Message[];
  inputValue: string;
  scrollPosition: number;
  currentConversationId: string | undefined;
  lastActivePath: string;
}

interface ChatContextType {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  inputValue: string;
  setInputValue: (value: string) => void;
  scrollPosition: number;
  setScrollPosition: (position: number) => void;
  currentConversationId: string | undefined;
  setCurrentConversationId: (id: string | undefined) => void;
  isRestored: boolean;
  saveState: () => void;
  clearState: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const STORAGE_KEY = 'chat-state-v1';

export function ChatProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValueState] = useState('');
  const [scrollPosition, setScrollPositionState] = useState(0);
  const [currentConversationId, setCurrentConversationIdState] = useState<string | undefined>();
  const [isRestored, setIsRestored] = useState(false);
  const [lastPath, setLastPath] = useState('');
  
  const scrollPosRef = useRef(0);

  // Load state from sessionStorage on mount
  useEffect(() => {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const state: ChatState = JSON.parse(stored);
        setMessages(state.messages || []);
        setInputValueState(state.inputValue || '');
        setScrollPositionState(state.scrollPosition || 0);
        scrollPosRef.current = state.scrollPosition || 0;
        setCurrentConversationIdState(state.currentConversationId);
        setLastPath(state.lastActivePath || '');
        setIsRestored(true);
      } catch {
        // Invalid stored state, ignore
      }
    }
  }, []);

  // Save state whenever it changes
  const saveState = useCallback(() => {
    const state: ChatState = {
      messages,
      inputValue,
      scrollPosition: scrollPosRef.current,
      currentConversationId,
      lastActivePath: pathname,
    };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [messages, inputValue, currentConversationId, pathname]);

  // Auto-save on changes
  useEffect(() => {
    saveState();
  }, [messages, inputValue, currentConversationId, saveState]);

  // Clear state
  const clearState = useCallback(() => {
    sessionStorage.removeItem(STORAGE_KEY);
    setMessages([]);
    setInputValueState('');
    setScrollPositionState(0);
    scrollPosRef.current = 0;
    setCurrentConversationIdState(undefined);
    setIsRestored(false);
  }, []);

  // Wrapper for setInputValue that also saves to localStorage for cross-session
  const setInputValue = useCallback((value: string) => {
    setInputValueState(value);
    // Also save to localStorage for drafts
    if (value) {
      localStorage.setItem('chat-draft-input', value);
    } else {
      localStorage.removeItem('chat-draft-input');
    }
  }, []);

  // Restore draft from localStorage on mount
  useEffect(() => {
    const draft = localStorage.getItem('chat-draft-input');
    if (draft && !inputValue) {
      setInputValueState(draft);
    }
  }, []);

  // Wrapper for setScrollPosition
  const setScrollPosition = useCallback((position: number) => {
    scrollPosRef.current = position;
    setScrollPositionState(position);
  }, []);

  // Wrapper for setCurrentConversationId
  const setCurrentConversationId = useCallback((id: string | undefined) => {
    setCurrentConversationIdState(id);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        inputValue,
        setInputValue,
        scrollPosition,
        setScrollPosition,
        currentConversationId,
        setCurrentConversationId,
        isRestored,
        saveState,
        clearState,
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
