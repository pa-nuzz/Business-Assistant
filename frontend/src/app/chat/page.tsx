"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { chat, user } from "@/lib/api";
import { useChat } from "@/components/chat-context";
import ChatMessage from "@/components/chat-message";
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
  WifiOff,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  created_at?: string;
  thinkingSteps?: string[];
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
  const urlConversationId = searchParams.get("id") || undefined;

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
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [activeSources, setActiveSources] = useState<Set<SourceType>>(new Set());
  const [userName, setUserName] = useState<string>("");
  const [, setHasInitialized] = useState(false);

  const [lastUserMessage, setLastUserMessage] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const streamingContentRef = useRef("");
  const currentConversationIdRef = useRef(contextConversationId);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isStreamingRef = useRef(isStreaming);
  const skipNextFetchRef = useRef(false);

  // Keep refs in sync with state
  useEffect(() => {
    currentConversationIdRef.current = contextConversationId;
  }, [contextConversationId]);

  useEffect(() => {
    isStreamingRef.current = isStreaming;
  }, [isStreaming]);

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


  

  const fetchConversation = useCallback(async (id: string) => {
    // Don't fetch if we're currently streaming
    if (isStreamingRef.current) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data: Conversation = await chat.getConversation(id);
      // Transform backend messages to our format
      setMessages(data.messages || []);
      setCurrentConversationId(id);
      setHasInitialized(true);
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes('Failed to fetch')) {
        setError("Backend server not reachable. Please ensure Django is running on http://127.0.0.1:8000");
      } else {
        setError("Failed to load conversation");
      }
      console.error("Error fetching conversation:", err);
    } finally {
      setIsLoading(false);
    }
  }, [setMessages, setCurrentConversationId]);

  // Fetch conversation history when id changes
  useEffect(() => {
    const id = searchParams.get("id");
    const query = searchParams.get("query");
    setCurrentConversationId(id || undefined);

    if (id) {
      // Skip fetch if we just created this conversation via streaming
      if (skipNextFetchRef.current) {
        skipNextFetchRef.current = false;
      } else {
        fetchConversation(id);
      }
    } else {
      // No ID in URL - show fresh chat on startup
      // Don't auto-load recent conversation - user wants fresh start
      setMessages([]);
      setError(null);
      // Clear any stored conversation ID
      setCurrentConversationId(undefined);
      if (query) {
        setInputValue(query);
      }
    }

    setHasInitialized(true);
  }, [searchParams, fetchConversation, setCurrentConversationId, setInputValue, setMessages]);

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

    // Build source modes from active toggles
    const sourceModes = Array.from(activeSources);

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
    setIsReconnecting(false);
    setRetryCount(0);
    streamingContentRef.current = "";

    // Add empty assistant message that will be filled as we stream
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", isStreaming: true },
    ]);

    // Streaming with exponential backoff retry
    const attemptStream = async (attempt: number): Promise<void> => {
      try {
        await chat.sendMessageStream(
          messageToSend + (sourceModes.length ? `\n[modes: ${sourceModes.join(',')}]` : ''),
          contextConversationId,
          (token) => {
            setRetryCount(0);
            setIsReconnecting(false);
            
            // Check for specialized thinking tokens: [THINK:Action...]
            if (token.startsWith('[THINK:') && token.endsWith(']')) {
              const step = token.substring(7, token.length - 1);
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage?.role === "assistant") {
                  if (!lastMessage.thinkingSteps) lastMessage.thinkingSteps = [];
                  if (!lastMessage.thinkingSteps.includes(step)) {
                    lastMessage.thinkingSteps = [...lastMessage.thinkingSteps, step];
                  }
                }
                return newMessages;
              });
              return;
            }

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
            if (metadata?.conversation_id && metadata.conversation_id !== currentConversationIdRef.current) {
              skipNextFetchRef.current = true;
              setCurrentConversationId(metadata.conversation_id);
              currentConversationIdRef.current = metadata.conversation_id;
              router.replace(`/chat?id=${metadata.conversation_id}`, { scroll: false });
            }
          },
          () => {
            setIsStreaming(false);
            setIsReconnecting(false);
            setRetryCount(0);
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage?.role === "assistant") {
                lastMessage.isStreaming = false;
              }
              return newMessages;
            });
            window.dispatchEvent(new CustomEvent("refresh-conversations"));
          },
          (err) => {
            if (attempt < 3 && (err.includes("Network Error") || err.includes("stream") || err.includes("timeout") || err.includes("Connection"))) {
              const delay = Math.min(1000 * Math.pow(2, attempt), 8000);
              setIsReconnecting(true);
              setRetryCount(attempt + 1);
              setTimeout(() => {
                attemptStream(attempt + 1);
              }, delay);
            } else {
              setError(err);
              setIsStreaming(false);
              setIsReconnecting(false);
              setRetryCount(0);
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
          }
        );
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error";
        if (attempt < 3 && (errorMessage.includes("Network") || errorMessage.includes("stream") || errorMessage.includes("Connection"))) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 8000);
          setIsReconnecting(true);
          setRetryCount(attempt + 1);
          setTimeout(() => {
            attemptStream(attempt + 1);
          }, delay);
        } else {
          setError(errorMessage);
          setIsStreaming(false);
          setIsReconnecting(false);
          setRetryCount(0);
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
      }
    };

    attemptStream(0);
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
      <div className="flex flex-col h-screen bg-white grid-dna">
      {/* Messages Area */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 pl-14 lg:pl-8 py-6 scroll-smooth"
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
                <img 
                  src="/logos/core.svg" 
                  alt="AEIOU AI" 
                  width={64} 
                  height={64}
                  className="drop-shadow-lg"
                />
              </motion.div>
              <motion.h1 
                className="text-2xl font-bold text-slate-900 mb-1 tracking-tight"
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
                I&apos;m <span className="font-semibold text-transparent bg-clip-text bg-linear-to-r from-indigo-600 to-violet-500">Aiden</span>, your AI Business Partner.
              </motion.p>
              <motion.p 
                className="text-slate-400 max-w-md mb-8 text-xs font-medium"
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.25, duration: 0.4 }}
              >
                I know your documents, tasks, and business context. Ask me anything.
              </motion.p>
              
              {/* Premium capability cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl w-full">
                {capabilityCards.map((card, idx) => {
                  const Icon = card.icon;
                  return (
                    <motion.button
                      key={idx}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 + idx * 0.08, duration: 0.4 }}
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleCardClick(card.prompt)}
                      className="flex flex-col items-start p-5 bg-white/70 backdrop-blur-xl border border-white/60 shadow-[0_4px_20px_rgb(0,0,0,0.03)] rounded-2xl hover:border-indigo-200/60 hover:shadow-[0_8px_30px_rgb(99,102,241,0.08)] cursor-pointer transition-all duration-300 text-left group"
                    >
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 transition-transform group-hover:scale-110 duration-300 shadow-sm border border-white/50 ${card.iconBg.replace('bg-', 'bg-linear-to-br from-white to-')}`}>
                        <Icon className={`w-5 h-5 ${card.iconColor}`} />
                      </div>
                      <h3 className="text-sm font-semibold text-slate-900 mb-1">{card.title}</h3>
                      <p className="text-xs text-slate-500 leading-relaxed font-medium">{card.description}</p>
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
                        className={`shadow-sm border border-white/50 ${
                          message.role === "user"
                            ? "bg-linear-to-br from-indigo-500 to-violet-600 text-white rounded-2xl rounded-tr-sm px-5 py-3.5"
                            : "bg-white/70 backdrop-blur-xl text-slate-800 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-[0_4px_20px_rgb(0,0,0,0.02)]"
                        }`}
                      >
                        {message.role === "assistant" ? (
                          <ChatMessage message={message} />
                        ) : (
                          <div className="text-[15px] leading-relaxed font-medium">{message.content}</div>
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

              {/* Reconnecting indicator */}
              {isReconnecting && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 text-sm text-muted-foreground mb-4"
                >
                  <WifiOff className="h-4 w-4 text-orange-500" />
                  <span>Connection interrupted. Retrying... (attempt {retryCount}/3)</span>
                </motion.div>
              )}

              {/* Typing indicator with animated logo and thinking steps */}
              {isStreaming && messages[messages.length - 1]?.role === "assistant" && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex flex-col items-start gap-1"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] font-semibold text-indigo-500 uppercase tracking-wide">Aiden is working</span>
                    <div className="flex gap-0.5">
                       <span className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                       <span className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                       <span className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                  
                  <div className="flex flex-col gap-2 w-full">
                    {/* Thinking Steps */}
                    <AnimatePresence>
                      {messages[messages.length - 1]?.thinkingSteps?.map((step, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          className="flex items-center gap-3 px-4 py-2 bg-slate-50 border border-slate-100 rounded-xl"
                        >
                          <div className="w-4 h-4 rounded-full bg-indigo-100 flex items-center justify-center">
                            <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />
                          </div>
                          <span className="text-xs text-slate-600 font-medium">{step}</span>
                          <Check className="w-3 h-3 text-emerald-500 ml-auto" />
                        </motion.div>
                      ))}
                    </AnimatePresence>

                    <div className="flex items-center gap-3 mt-1">
                      <div className="w-6 h-6 shrink-0">
                        <img src="/logos/core.svg" alt="" width={24} height={24} />
                      </div>
                      {!messages[messages.length - 1]?.content && (
                        <div className="bg-slate-100 rounded-2xl rounded-bl-sm px-4 py-2.5">
                          <span className="text-xs text-slate-400 italic">Synthesizing response...</span>
                        </div>
                      )}
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

      {/* Input Area - Sticky dock design, auto-adjusts to sidebar width */}
      <div className="sticky bottom-0 bg-linear-to-t from-white via-white/90 to-transparent pt-12 pb-6 px-4 sm:px-6 lg:px-8 pl-14 lg:pl-8 z-10 pointer-events-none">
        <div className="max-w-3xl mx-auto pointer-events-auto">
          <div className="bg-white/70 backdrop-blur-2xl border border-white/60 shadow-[0_8px_30px_rgb(0,0,0,0.06)] rounded-3xl overflow-hidden transition-all duration-300 focus-within:shadow-[0_8px_30px_rgb(99,102,241,0.12)] focus-within:border-indigo-200/50">
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
                  className="p-2.5 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed rounded-full hover:bg-slate-100/50"
                >
                  <Mic className="w-4 h-4" />
                </button>
                {isStreaming ? (
                  <div className="w-10 h-10 flex items-center justify-center">
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
                    className={`w-12 h-12 flex items-center justify-center rounded-2xl transition-all duration-300 ${
                      inputValue.trim() && !isStreaming
                        ? "bg-linear-to-br from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/20 hover:scale-105 active:scale-95"
                        : "bg-slate-100 text-slate-400 cursor-not-allowed"
                    }`}
                  >
                    <ArrowUp className="w-5 h-5" />
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
