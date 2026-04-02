"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { chat, user } from "@/lib/api";
import { OnboardingWizard } from "@/components/onboarding-wizard";
import { useChat } from "@/components/chat-context";
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
  Copy,
  Check,
  RefreshCw,
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

  // Use ChatContext for persistent state
  const {
    messages,
    setMessages,
    inputValue,
    setInputValue,
    scrollPosition,
    setScrollPosition,
    currentConversationId: contextConversationId,
    setCurrentConversationId,
    isRestored,
    saveState,
  } = useChat();

  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSources, setActiveSources] = useState<Set<SourceType>>(new Set());
  const [userName, setUserName] = useState<string>("");
  const [hasInitialized, setHasInitialized] = useState(false);

  const [lastUserMessage, setLastUserMessage] = useState<string>("");
  const [showOnboarding, setShowOnboarding] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const streamingContentRef = useRef("");
  const currentConversationIdRef = useRef(contextConversationId);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isInitialMount = useRef(true);

  const { pop, chime } = useSoundEffects();

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

  // Track scroll position
  const handleScroll = useCallback(() => {
    if (messagesContainerRef.current) {
      setScrollPosition(messagesContainerRef.current.scrollTop);
    }
  }, [setScrollPosition]);

  // Fetch conversation history when id changes
  useEffect(() => {
    const id = searchParams.get("id");
    setCurrentConversationId(id || undefined);

    if (id) {
      // Only fetch if we haven't restored from context or if it's a different conversation
      if (!isRestored || contextConversationId !== id) {
        fetchConversation(id);
      }
    } else {
      // Only clear messages if we're not restoring from context
      if (!isRestored || isInitialMount.current) {
        setMessages([]);
        setError(null);
      }
    }
    
    isInitialMount.current = false;
    setHasInitialized(true);
  }, [searchParams]);

  // Restore scroll position after messages load
  useEffect(() => {
    if (messagesContainerRef.current && scrollPosition > 0 && !isLoading) {
      messagesContainerRef.current.scrollTop = scrollPosition;
    }
  }, [messages.length, isLoading, scrollPosition]);

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

    // Play pop sound on send
    pop();

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

    // Add 3-4 second "thinking" delay for natural feel (random between 3-4s)
    const thinkingDelay = 3000 + Math.random() * 1000;
    await new Promise(resolve => setTimeout(resolve, thinkingDelay));

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
          // Save state after message complete
          saveState();
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
      description: "Upload PDFs and ask questions about them",
      color: "blue",
      prompt: "I have a document I'd like to analyze. Can you help me understand it?",
    },
    {
      icon: CheckSquare,
      title: "Manage tasks",
      description: "Create and track your business tasks",
      color: "green",
      prompt: "Help me create a task list for my business priorities.",
    },
    {
      icon: BarChart3,
      title: "Business insights",
      description: "Get AI analysis of your metrics and KPIs",
      color: "purple",
      prompt: "Can you help me analyze my business performance and metrics?",
    },
    {
      icon: Globe,
      title: "Market research",
      description: "Search and summarize industry trends",
      color: "orange",
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
      <div className="flex flex-col h-[calc(100vh-4rem)] bg-background">
      {/* Messages Area */}
      <div 
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6"
      >
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
            // Empty state with welcome UI - premium design
            <div className="flex flex-col items-center justify-center pt-[3%] min-h-[400px] text-center">
              <div className="w-20 h-20 mb-6 relative" style={{ filter: 'drop-shadow(0 0 40px rgba(59,130,246,0.15))' }}>
                <img 
                  src="/logos/core.svg" 
                  alt="AEIOU AI" 
                  className="w-full h-full object-contain"
                />
              </div>
              <h1 className="text-2xl font-semibold text-foreground mb-2">
                {getGreeting()}{userName ? `, ${userName}` : ""}
              </h1>
              <p className="text-muted-foreground max-w-md mb-8">
                What can I help you with today?
              </p>
              
              {/* Capability cards - 2x2 grid */}
              <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
                {capabilityCards.map((card, idx) => {
                  const Icon = card.icon;
                  const colorClasses: Record<string, { bg: string; text: string }> = {
                    blue: { bg: "bg-blue-50", text: "text-blue-600" },
                    green: { bg: "bg-green-50", text: "text-green-600" },
                    purple: { bg: "bg-purple-50", text: "text-purple-600" },
                    orange: { bg: "bg-orange-50", text: "text-orange-600" },
                  };
                  const colors = colorClasses[card.color];
                  return (
                    <motion.button
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      onClick={() => handleCardClick(card.prompt)}
                      className="flex flex-col items-start p-4 bg-card border border-border rounded-xl hover:border-blue-300 hover:shadow-sm cursor-pointer transition-all text-left"
                    >
                      <div className={`w-10 h-10 rounded-lg ${colors.bg} flex items-center justify-center mb-3`}>
                        <Icon className={`w-5 h-5 ${colors.text}`} />
                      </div>
                      <h3 className="text-sm font-medium text-foreground mb-1">{card.title}</h3>
                      <p className="text-xs text-muted-foreground leading-relaxed">{card.description}</p>
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
                    className={`flex flex-col ${
                      message.role === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    <div className="relative group max-w-[85%] sm:max-w-[75%]">
                      <div
                        className={`${
                          message.role === "user"
                            ? "bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-2.5 shadow-sm"
                            : "bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm"
                        }`}
                      >
                        {message.role === "assistant" ? (
                          <div className="prose prose-sm max-w-none dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 prose-p:my-1">
                            <ReactMarkdown>
                              {message.content}
                            </ReactMarkdown>
                            {message.isStreaming && (
                              <motion.span
                                animate={{ opacity: [1, 0, 1] }}
                                transition={{ duration: 0.8, repeat: Infinity }}
                                className="inline-block w-0.5 h-4 bg-foreground ml-0.5 align-middle"
                              />
                            )}
                          </div>
                        ) : (
                          <p className="text-sm leading-relaxed">{message.content}</p>
                        )}
                      </div>
                      {/* Copy button for assistant messages */}
                      {message.role === "assistant" && !message.isStreaming && message.content && (
                        <button
                          onClick={() => handleCopy(message.content, index)}
                          className="absolute -top-2 -right-2 p-1.5 bg-white border border-gray-200 rounded-lg shadow-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-50"
                          title="Copy to clipboard"
                        >
                          {copiedIndex === index ? (
                            <Check className="w-3.5 h-3.5 text-green-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5 text-gray-500" />
                          )}
                        </button>
                      )}
                    </div>
                    {/* Timestamp */}
                    {message.created_at && (
                      <span className="text-xs text-muted-foreground mt-1 px-1">
                        {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    )}
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
                  className="flex flex-col items-center gap-2"
                >
                  <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-lg text-sm">
                    {typeof error === 'string' ? error : 'An error occurred'}
                  </div>
                  <button
                    onClick={() => handleRetry()}
                    className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
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
                    onClick={() => handleSend()}
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
      {showOnboarding && (
        <OnboardingWizard onClose={() => setShowOnboarding(false)} />
      )}
    </>
  );
}

