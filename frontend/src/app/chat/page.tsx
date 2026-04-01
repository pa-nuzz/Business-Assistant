"use client";

import React, { useState, useEffect, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { chat, user } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import {
  Search,
  Mic,
  ArrowUp,
  BrainCircuit,
  CircleDot,
  FileText,
  CheckSquare,
  BarChart3,
  Globe,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { TypingIndicator } from "@/components/typing-indicator";
import { useSoundEffects } from "@/components/sound-effects";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  created_at?: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

type SourceType = "search" | "deep_research" | "reason";

export default function ChatPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const conversationId = searchParams.get("id") || undefined;

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSources, setActiveSources] = useState<Set<SourceType>>(new Set());
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(conversationId);
  const [userName, setUserName] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const streamingContentRef = useRef("");
  const currentConversationIdRef = useRef(currentConversationId);

  const { pop, chime } = useSoundEffects();

  // Keep ref in sync with state
  useEffect(() => {
    currentConversationIdRef.current = currentConversationId;
  }, [currentConversationId]);

  // Fetch user info on mount
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const data = await user.getInfo();
        if (data.username) {
          setUserName(data.username);
        } else {
          // Fallback to localStorage
          const token = localStorage.getItem('access_token');
          if (token) {
            const payload = JSON.parse(atob(token.split('.')[1]));
            setUserName(payload.username || "");
          }
        }
      } catch {
        // Fallback to localStorage
        const token = localStorage.getItem('access_token');
        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            setUserName(payload.username || "");
          } catch {
            setUserName("");
          }
        }
      }
    };
    fetchUserInfo();
  }, []);

  // Fetch conversation history when id changes
  useEffect(() => {
    const id = searchParams.get("id");
    setCurrentConversationId(id || undefined);

    if (id) {
      fetchConversation(id);
    } else {
      setMessages([]);
      setError(null);
    }
  }, [searchParams]);

  const fetchConversation = async (id: string) => {
    // Don't fetch if we're currently streaming or have messages for this conversation
    // This prevents overwriting streamed messages with stale API data
    if (isStreaming || (currentConversationIdRef.current === id && messages.length > 0)) {
      return;
    }
    
    setIsLoading(true);
    setError(null);
    try {
      const data: Conversation = await chat.getConversation(id);
      // Transform backend messages to our format
      const formattedMessages: Message[] = data.messages.map((msg: any) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        created_at: msg.created_at,
      }));
      // Only set messages if we got valid data
      if (formattedMessages.length > 0) {
        setMessages(formattedMessages);
      }
    } catch (err) {
      setError("Failed to load conversation");
      console.error("Error fetching conversation:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  const toggleSource = (source: SourceType) => {
    setActiveSources((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(source)) {
        newSet.delete(source);
      } else {
        newSet.add(source);
      }
      return newSet;
    });
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isStreaming) return;

    // Play pop sound on send
    pop();

    const userMessage: Message = {
      role: "user",
      content: inputValue.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsStreaming(true);
    setError(null);
    streamingContentRef.current = "";

    // Add empty assistant message that will be filled as we stream
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", isStreaming: true },
    ]);

    try {
      await chat.sendMessageStream(
        userMessage.content,
        currentConversationId,
        (token) => {
          streamingContentRef.current += token;
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage?.role === "assistant") {
              lastMessage.content = streamingContentRef.current;
            }
            return newMessages;
          });
        },
        (metadata) => {
          // Update URL with new conversation_id if provided
          // Use ref to get latest value, not stale closure
          if (metadata?.conversation_id && metadata.conversation_id !== currentConversationIdRef.current) {
            setCurrentConversationId(metadata.conversation_id);
            currentConversationIdRef.current = metadata.conversation_id; // Update ref immediately
            router.replace(`/chat?id=${metadata.conversation_id}`, { scroll: false });
          }
        },
        () => {
          // Streaming done
          setIsStreaming(false);
          // Play chime sound on receive
          chime();
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage?.role === "assistant") {
              lastMessage.isStreaming = false;
            }
            return newMessages;
          });
          // Trigger sidebar refresh
          window.dispatchEvent(new CustomEvent("refresh-conversations"));
        },
        (err) => {
          setError(err);
          setIsStreaming(false);
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage?.role === "assistant") {
              lastMessage.isStreaming = false;
              lastMessage.content = streamingContentRef.current || "Error: " + err;
            }
            return newMessages;
          });
        }
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(errorMessage);
      setIsStreaming(false);
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage?.role === "assistant") {
          lastMessage.isStreaming = false;
          lastMessage.content = "Error: " + errorMessage;
        }
        return newMessages;
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (text: string) => {
    setInputValue(text);
    // Use setTimeout to ensure state is updated before sending
    setTimeout(() => {
      handleSend();
    }, 50);
  };

  const suggestions = [
    { text: "Summarize my documents", icon: FileText },
    { text: "What are my pending tasks?", icon: CheckSquare },
    { text: "Show my business metrics", icon: BarChart3 },
    { text: "Search the web for market trends", icon: Globe },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-background">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-3xl mx-auto">
          {isLoading ? (
            // Loading skeleton
            <div className="space-y-6">
              <div className="flex justify-end">
                <div className="skeleton w-3/4 h-12" />
              </div>
              <div className="flex justify-start">
                <div className="skeleton w-full h-24" />
              </div>
              <div className="flex justify-end">
                <div className="skeleton w-1/2 h-12" />
              </div>
              <div className="flex justify-start">
                <div className="skeleton w-3/4 h-20" />
              </div>
            </div>
          ) : messages.length === 0 ? (
            // Empty state with welcome UI - positioned down
            <div className="flex flex-col items-center justify-center pt-[3%] min-h-[400px] text-center">
              <div className="w-24 h-24 mb-6 relative">
                <img 
                  src="/logos/core.svg" 
                  alt="AEIOU AI" 
                  className="w-full h-full object-contain"
                />
              </div>
              <h1 className="text-2xl font-semibold text-foreground mb-2">
                {userName ? `Welcome back, ${userName}` : "Ready to assist you"}
              </h1>
              <p className="text-muted-foreground max-w-md mb-8">
                Ask me anything or choose a suggestion below to get started
              </p>
              
              {/* Suggestion chips */}
              <div className="flex flex-wrap justify-center gap-3 max-w-lg">
                {suggestions.map((suggestion, idx) => {
                  const Icon = suggestion.icon;
                  return (
                    <motion.button
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      onClick={() => handleSuggestionClick(suggestion.text)}
                      className="flex items-center gap-2 px-4 py-2.5 bg-card border border-border rounded-xl text-sm text-foreground hover:border-blue-300 hover:bg-blue-50/50 transition-all"
                    >
                      <Icon className="w-4 h-4 text-blue-600" />
                      {suggestion.text}
                    </motion.button>
                  );
                })}
              </div>
            </div>
          ) : (
            // Messages list
            <div className="space-y-6">
              <AnimatePresence initial={false}>
                {messages.map((message, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25, ease: "easeOut" }}
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[85%] sm:max-w-[75%] ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-3"
                          : "text-foreground px-1"
                      }`}
                    >
                      {message.role === "assistant" ? (
                        <div className="prose prose-sm max-w-none dark:prose-invert prose-p:leading-relaxed prose-pre:p-0">
                          <ReactMarkdown>
                            {message.content + (message.isStreaming ? "" : "")}
                          </ReactMarkdown>
                          {message.isStreaming && (
                            <span className="inline-block w-2 h-4 ml-0.5 bg-current animate-pulse" />
                          )}
                        </div>
                      ) : (
                        <p className="text-sm leading-relaxed">{message.content}</p>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {/* Typing indicator when AI is thinking */}
              {isStreaming && messages[messages.length - 1]?.role === "assistant" && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                    <TypingIndicator />
                  </div>
                </motion.div>
              )}
              
              {error && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-center"
                >
                  <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-lg text-sm">
                    {error}
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-background px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="bg-card border border-border rounded-xl shadow-sm">
            {/* Text input */}
            <div className="px-4 pt-4">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                disabled={isStreaming}
                rows={1}
                className="w-full bg-transparent text-foreground placeholder:text-muted-foreground resize-none outline-none min-h-[24px] max-h-[200px] text-sm leading-relaxed"
              />
            </div>

            {/* Controls */}
            <div className="px-3 py-3 flex items-center justify-between">
              {/* Source toggles */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleSource("search")}
                  disabled={isStreaming}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    activeSources.has("search")
                      ? "bg-accent-blue-subtle text-accent-blue"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>Search</span>
                </button>
                <button
                  onClick={() => toggleSource("deep_research")}
                  disabled={isStreaming}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    activeSources.has("deep_research")
                      ? "bg-accent-blue-subtle text-accent-blue"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  <CircleDot className="w-3.5 h-3.5" />
                  <span>Deep Research</span>
                </button>
                <button
                  onClick={() => toggleSource("reason")}
                  disabled={isStreaming}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    activeSources.has("reason")
                      ? "bg-accent-blue-subtle text-accent-blue"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  <BrainCircuit className="w-3.5 h-3.5" />
                  <span>Reason</span>
                </button>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2">
                <button
                  disabled={isStreaming}
                  className="p-2 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Mic className="w-4 h-4" />
                </button>
                {isStreaming ? (
                  <div className="w-8 h-8 flex items-center justify-center">
                    <TypingIndicator />
                  </div>
                ) : (
                  <button
                    onClick={handleSend}
                    disabled={!inputValue.trim() || isStreaming}
                    className={`w-8 h-8 flex items-center justify-center rounded-full transition-colors ${
                      inputValue.trim() && !isStreaming
                        ? "bg-primary text-primary-foreground hover:bg-primary/90"
                        : "bg-muted text-muted-foreground cursor-not-allowed"
                    }`}
                  >
                    <ArrowUp className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <p className="text-center text-xs text-muted-foreground mt-3">
            AI-generated content may contain inaccuracies. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}

