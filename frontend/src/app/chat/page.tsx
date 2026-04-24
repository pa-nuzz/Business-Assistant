"use client";

import React, { useState, useEffect, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { chat, user } from "@/lib/api";
import { useChat } from "@/components/chat-context";
import ReactMarkdown from "react-markdown";
import {
  Search,
  Mic,
  ArrowUp,
  BrainCircuit,
  Sparkles,
  FileText,
  CheckSquare,
  BarChart3,
  Globe,
  Copy,
  Check,
  RefreshCw,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
  const _conversationId = searchParams.get("id") || undefined;

  // Use ChatContext for persistent state
  const {
    messages,
    setMessages,
    inputValue,
    setInputValue,
    currentConversationId: contextConversationId,
    setCurrentConversationId,
  } = useChat();

  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSources, setActiveSources] = useState<Set<SourceType>>(new Set());
  const [userName, setUserName] = useState<string>("");
  const [, setHasInitialized] = useState(false);

  const [lastUserMessage, setLastUserMessage] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const streamingContentRef = useRef("");
  const currentConversationIdRef = useRef(contextConversationId);
  const messagesContainerRef = useRef<HTMLDivElement>(null);


  // Keep ref in sync with state
  useEffect(() => {
    currentConversationIdRef.current = contextConversationId;
  }, [contextConversationId]);

  // Fetch user info on mount
  useEffect(() => {
    document.title = 'Chat | AEIOU AI';
  }, []);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const data = await user.getInfo();
        if (data.username) {
          setUserName(data.username);
        }
      } catch {
        // Silently fail - username not critical for chat
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
      // No ID in URL - show fresh chat on startup
      // Don't auto-load recent conversation - user wants fresh start
      setMessages([]);
      setError(null);
      // Clear any stored conversation ID
      setCurrentConversationId(undefined);
    }
    
    setHasInitialized(true);
  }, [searchParams]);


  const fetchConversation = async (id: string) => {
    // Don't fetch if we're currently streaming
    if (isStreaming) {
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
      const axiosError = err as any;
      if (!axiosError.response && axiosError.message?.includes('Network Error')) {
        setError("Backend server not reachable. Please ensure Django is running on http://127.0.0.1:8000");
      } else {
        setError("Failed to load conversation");
      }
      console.error("Error fetching conversation:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const _loadRecentConversation = async () => {
    if (isStreaming) return;

    setIsLoading(true);
    try {
      const data = await chat.getConversations(1, 1); // Get most recent
      if (data.results && data.results.length > 0) {
        const recentId = data.results[0].id;
        // Navigate to the recent conversation
        router.replace(`/chat?id=${recentId}`, { scroll: false });
      } else {
        // No conversations exist, clear messages
        setMessages([]);
        setError(null);
      }
    } catch (err) {
      // Silently fail - show empty state
      setMessages([]);
      setError(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-scroll to bottom only when streaming new messages
  useEffect(() => {
    if (isStreaming) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, isStreaming]);

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

  const handleSend = async (retryMessage?: string) => {
    const messageToSend = retryMessage || inputValue.trim();
    if (!messageToSend || isStreaming) return;

    // Store last user message for retry
    if (!retryMessage) {
      setLastUserMessage(messageToSend);
    }


    const userMessage: Message = {
      role: "user",
      content: messageToSend,
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!retryMessage) {
      setInputValue("");
    }
    setIsStreaming(true);
    setError(null);
    streamingContentRef.current = "";

    // Add empty assistant message that will be filled as we stream
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", isStreaming: true },
    ]);

    // Small animation grace period only on first message
    if (messages.length <= 1) {
      await new Promise(resolve => setTimeout(resolve, 400));
    }

    try {
      await chat.sendMessageStream(
        messageToSend,
        contextConversationId,
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

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  const capabilityCards = [
    {
      icon: FileText,
      title: "Analyze documents",
      description: "Contracts, reports, financials — I extract insights",
      iconBg: "bg-blue-50",
      iconColor: "text-blue-600",
      prompt: "I have a document I'd like to analyze. Can you help me understand it?",
    },
    {
      icon: CheckSquare,
      title: "Manage tasks",
      description: "Create and track your business tasks",
      iconBg: "bg-green-50",
      iconColor: "text-green-600",
      prompt: "Help me create a task list for my business priorities.",
    },
    {
      icon: BarChart3,
      title: "Business insights",
      description: "Get AI analysis of your metrics and KPIs",
      iconBg: "bg-purple-50",
      iconColor: "text-purple-600",
      prompt: "Can you help me analyze my business performance and metrics?",
    },
    {
      icon: Globe,
      title: "Market research",
      description: "Search and summarize industry trends",
      iconBg: "bg-orange-50",
      iconColor: "text-orange-600",
      prompt: "What are the current trends in my industry?",
    },
  ];

  const handleCardClick = (prompt: string) => {
    setInputValue(prompt);
    inputRef.current?.focus();
  };

  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopy = async (content: string, index: number) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 1500);
    } catch {
      // Ignore copy errors
    }
  };

  const handleRetry = () => {
    if (lastUserMessage) {
      // Remove the error message and last assistant message
      setMessages((prev) => {
        const newMessages = [...prev];
        // Remove last assistant message with error
        if (newMessages.length > 0 && newMessages[newMessages.length - 1]?.role === "assistant") {
          newMessages.pop();
        }
        return newMessages;
      });
      setError(null);
      // Retry with stored message
      handleSend(lastUserMessage);
    }
  };

  return (
    <>
      <div className="flex flex-col h-screen bg-slate-50">
      {/* Messages Area - Added pl-14 for mobile to account for hamburger button */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 pl-14 sm:pl-6 py-6 scroll-smooth"
      >
        <div className="max-w-3xl mx-auto pb-40">
          {isLoading ? (
            // Clean loading skeleton
            <div className="space-y-6">
              <div className="flex justify-end">
                <div className="w-3/4 h-12 rounded-2xl bg-indigo-100 animate-pulse" />
              </div>
              <div className="flex justify-start">
                <div className="w-full h-24 rounded-2xl bg-slate-100 animate-pulse" />
              </div>
              <div className="flex justify-end">
                <div className="w-1/2 h-12 rounded-2xl bg-indigo-100 animate-pulse" />
              </div>
              <div className="flex justify-start">
                <div className="w-3/4 h-20 rounded-2xl bg-slate-100 animate-pulse" />
              </div>
            </div>
          ) : messages.length === 0 ? (
            // Clean empty state with animated logo
            <div className="flex flex-col items-center justify-center pt-[10vh] min-h-[400px] text-center px-4 sm:px-0">
              <motion.div 
                className="w-16 h-16 mb-5 flex items-center justify-center"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              >
                <svg 
                  width="64" 
                  height="64" 
                  viewBox="0 0 100 100" 
                  fill="none" 
                  xmlns="http://www.w3.org/2000/svg"
                  className="drop-shadow-lg"
                >
                  <circle cx="50" cy="50" r="48" fill="white"/>
                  <circle cx="50" cy="50" r="48" fill="url(#brandGradient)" fillOpacity="0.1"/>
                  <rect x="20" y="45" width="8" height="35" rx="4" fill="#6366F1">
                    <animate attributeName="height" values="35;25;45;35" dur="3s" repeatCount="indefinite" />
                    <animate attributeName="y" values="45;55;35;45" dur="3s" repeatCount="indefinite" />
                  </rect>
                  <rect x="35" y="30" width="8" height="50" rx="4" fill="#8B5CF6">
                    <animate attributeName="height" values="50;35;55;50" dur="2.5s" repeatCount="indefinite" />
                    <animate attributeName="y" values="30;45;25;30" dur="2.5s" repeatCount="indefinite" />
                  </rect>
                  <rect x="50" y="20" width="8" height="60" rx="4" fill="#6366F1">
                    <animate attributeName="height" values="60;40;70;60" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="y" values="20;40;10;20" dur="2s" repeatCount="indefinite" />
                  </rect>
                  <rect x="65" y="35" width="8" height="45" rx="4" fill="#8B5CF6">
                    <animate attributeName="height" values="45;30;50;45" dur="2.7s" repeatCount="indefinite" />
                    <animate attributeName="y" values="35;50;25;35" dur="2.7s" repeatCount="indefinite" />
                  </rect>
                  <rect x="80" y="50" width="8" height="30" rx="4" fill="#6366F1">
                    <animate attributeName="height" values="30;20;40;30" dur="3.2s" repeatCount="indefinite" />
                    <animate attributeName="y" values="50;60;40;50" dur="3.2s" repeatCount="indefinite" />
                  </rect>
                  <defs>
                    <linearGradient id="brandGradient" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#6366F1"/>
                      <stop offset="1" stopColor="#8B5CF6"/>
                    </linearGradient>
                  </defs>
                </svg>
              </motion.div>
              <motion.h1 
                className="text-xl font-semibold text-slate-900 mb-1"
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1, duration: 0.4 }}
              >
                {getGreeting()}{userName ? `, ${userName}` : ""}
              </motion.h1>
              <motion.p 
                className="text-slate-500 max-w-md mb-2 text-sm"
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.4 }}
              >
                I'm <span className="font-semibold text-indigo-600">Aiden</span>, your AI Business Partner.
              </motion.p>
              <motion.p 
                className="text-slate-400 max-w-md mb-8 text-xs"
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.25, duration: 0.4 }}
              >
                I know your documents, tasks, and business context. Ask me anything.
              </motion.p>
              
              {/* Clean capability cards */}
              <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
                {capabilityCards.map((card, idx) => {
                  const Icon = card.icon;
                  return (
                    <motion.button
                      key={idx}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 + idx * 0.08, duration: 0.4 }}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => handleCardClick(card.prompt)}
                      className="flex flex-col items-start p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-300 hover:shadow-md cursor-pointer transition-all text-left group"
                    >
                      <div className={`w-9 h-9 rounded-lg ${card.iconBg} flex items-center justify-center mb-3 bg-slate-100`}>
                        <Icon className={`w-4 h-4 ${card.iconColor}`} />
                      </div>
                      <h3 className="text-sm font-medium text-slate-900 mb-0.5">{card.title}</h3>
                      <p className="text-xs text-slate-500 leading-relaxed">{card.description}</p>
                    </motion.button>
                  );
                })}
              </div>
            </div>
          ) : (
            // Messages list with premium styling
            <div className="space-y-6">
              <AnimatePresence initial={false}>
                {messages.map((message, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
                    className={`flex flex-col ${
                      message.role === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    {/* Sender label */}
                    <div className="flex items-center gap-1 mb-1">
                      {message.role === "assistant" && (
                        <span className="text-[10px] font-semibold text-indigo-500 uppercase tracking-wide">Aiden</span>
                      )}
                    </div>
                    <div className="relative group max-w-[85%] sm:max-w-[75%]">
                      <div
                        className={`${
                          message.role === "user"
                            ? "bg-indigo-600 text-white rounded-2xl rounded-br-sm px-4 py-2.5 shadow-sm"
                            : "bg-slate-100 text-slate-900 rounded-2xl rounded-bl-sm px-4 py-2.5"
                        }`}
                      >
                        {message.role === "assistant" ? (
                          <div className="prose prose-sm max-w-none prose-p:leading-relaxed prose-pre:p-0 prose-p:my-1 text-slate-800">
                            {message.isStreaming ? (
                              <div className="text-sm leading-relaxed whitespace-pre-wrap flex items-end">
                                {message.content}
                                <span className="inline-block w-0.5 h-4 bg-indigo-500 ml-0.5 animate-pulse" />
                              </div>
                            ) : (
                              <ReactMarkdown>{message.content}</ReactMarkdown>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                        )}
                      </div>
                      {/* Copy button for assistant messages */}
                      {message.role === "assistant" && !message.isStreaming && message.content && (
                        <motion.button
                          onClick={() => handleCopy(message.content, index)}
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 0, scale: 0.8 }}
                          whileHover={{ opacity: 1, scale: 1 }}
                          className="absolute -top-2 -right-2 p-1.5 bg-white border border-slate-200 rounded-lg shadow-sm opacity-0 group-hover:opacity-100 transition-all hover:bg-slate-50"
                          title="Copy to clipboard"
                        >
                          {copiedIndex === index ? (
                            <Check className="w-3.5 h-3.5 text-emerald-500" />
                          ) : (
                            <Copy className="w-3.5 h-3.5 text-slate-400" />
                          )}
                        </motion.button>
                      )}
                    </div>
                    {/* Timestamp */}
                    {message.created_at && (
                      <span className="text-[11px] text-slate-400 mt-1 px-1">
                        {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {/* Typing indicator with animated logo */}
              {isStreaming && messages[messages.length - 1]?.role === "assistant" && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex flex-col items-start gap-1"
                >
                  <span className="text-[10px] font-semibold text-indigo-500 uppercase tracking-wide">Aiden is typing...</span>
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 flex-shrink-0">
                      <svg width="24" height="24" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="15" y="50" width="10" height="30" rx="5" fill="#6366F1">
                          <animate attributeName="height" values="30;20;35;30" dur="3s" repeatCount="indefinite" />
                          <animate attributeName="y" values="50;60;45;50" dur="3s" repeatCount="indefinite" />
                        </rect>
                        <rect x="35" y="35" width="10" height="50" rx="5" fill="#8B5CF6">
                          <animate attributeName="height" values="50;35;55;50" dur="2.5s" repeatCount="indefinite" />
                          <animate attributeName="y" values="35;50;30;35" dur="2.5s" repeatCount="indefinite" />
                        </rect>
                        <rect x="55" y="25" width="10" height="60" rx="5" fill="#6366F1">
                          <animate attributeName="height" values="60;40;70;60" dur="2s" repeatCount="indefinite" />
                          <animate attributeName="y" values="25;45;15;25" dur="2s" repeatCount="indefinite" />
                        </rect>
                        <rect x="75" y="45" width="10" height="35" rx="5" fill="#8B5CF6">
                          <animate attributeName="height" values="35;25;40;35" dur="2.7s" repeatCount="indefinite" />
                          <animate attributeName="y" values="45;55;40;45" dur="2.7s" repeatCount="indefinite" />
                        </rect>
                      </svg>
                    </div>
                    <div className="bg-slate-100 rounded-2xl rounded-bl-sm px-4 py-2.5 flex items-center gap-2">
                      <div className="flex gap-1">
                        <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
              
              {/* Error display with retry */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex flex-col items-center gap-3"
                >
                  <div className="bg-red-50 text-red-600 border border-red-100 px-4 py-2.5 rounded-lg text-sm font-medium">
                    {typeof error === 'string' ? error : 'An error occurred'}
                  </div>
                  <button
                    onClick={() => handleRetry()}
                    className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 transition-colors px-3 py-1.5 rounded-full hover:bg-slate-100"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Retry
                  </button>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Area - Fixed at bottom with proper mobile spacing */}
      <div className="fixed bottom-0 left-0 right-0 lg:left-[280px] border-t border-slate-200 bg-white px-4 sm:px-6 lg:px-8 pl-14 sm:pl-6 py-4 z-10">
        <div className="max-w-3xl mx-auto">
          <div className="bg-slate-50 border border-slate-200 rounded-xl shadow-sm">
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
                className="w-full bg-transparent text-slate-900 placeholder:text-slate-400 resize-none outline-none min-h-[24px] max-h-[200px] text-sm leading-relaxed"
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
                      ? "bg-indigo-50 text-indigo-600 border border-indigo-200"
                      : "bg-white text-slate-500 hover:bg-slate-100 border border-slate-200"
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
                      ? "bg-purple-50 text-purple-600 border border-purple-200"
                      : "bg-white text-slate-500 hover:bg-slate-100 border border-slate-200"
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Deep Research</span>
                </button>
                <button
                  onClick={() => toggleSource("reason")}
                  disabled={isStreaming}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    activeSources.has("reason")
                      ? "bg-green-50 text-green-600 border border-green-200"
                      : "bg-white text-slate-500 hover:bg-slate-100 border border-slate-200"
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
                  className="p-2 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Mic className="w-4 h-4" />
                </button>
                {isStreaming ? (
                  <div className="w-8 h-8 flex items-center justify-center">
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => handleSend()}
                    disabled={!inputValue.trim() || isStreaming}
                    className={`w-9 h-9 flex items-center justify-center rounded-lg transition-all duration-150 ${
                      inputValue.trim() && !isStreaming
                        ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm"
                        : "bg-slate-200 text-slate-400 cursor-not-allowed"
                    }`}
                  >
                    <ArrowUp className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <p className="text-center text-xs text-slate-400 mt-3">
            AI-generated content may contain inaccuracies. Verify important information. • 
            <button 
              onClick={() => window.dispatchEvent(new CustomEvent('open-help'))}
              className="hover:text-indigo-500 underline underline-offset-2"
            >
              Keyboard shortcuts
            </button>
          </p>
        </div>
      </div>
    </div>
    </>
  );
}
