"use client";

import { useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";
import { Copy, Check, Link2 } from "lucide-react";
import { motion } from "framer-motion";

interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  created_at?: string;
  citations?: Citation[];
}

interface Citation {
  index: number;
  title: string;
  url?: string;
  snippet?: string;
}

interface ChatMessageProps {
  message: Message;
}

function CopyButton({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  }, [code]);

  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 p-1.5 rounded-md bg-white/10 hover:bg-white/20 text-white/70 hover:text-white transition-all opacity-0 group-hover:opacity-100"
      title="Copy code"
    >
      {copied ? (
        <Check className="h-4 w-4 text-emerald-400" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
    </button>
  );
}

function CitationBadge({ citation }: { citation: Citation }) {
  return (
    <a
      href={citation.url || "#"}
      target={citation.url ? "_blank" : undefined}
      rel={citation.url ? "noopener noreferrer" : undefined}
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-primary/10 text-primary hover:bg-primary/20 transition-colors no-underline"
      title={citation.title}
    >
      <Link2 className="h-3 w-3" />
      {citation.index}
    </a>
  );
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
    >
      <div
        className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-muted text-foreground rounded-bl-md"
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || "");
                  const code = String(children).replace(/\n$/, "");

                  if (!inline && match) {
                    return (
                      <div className="relative group my-3">
                        <div className="flex items-center justify-between px-3 py-1.5 bg-slate-800 rounded-t-md">
                          <span className="text-xs text-slate-400 font-mono">
                            {match[1]}
                          </span>
                          <CopyButton code={code} />
                        </div>
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                          customStyle={{
                            margin: 0,
                            borderRadius: "0 0 6px 6px",
                            padding: "1rem",
                            fontSize: "0.85rem",
                            lineHeight: "1.5",
                          }}
                          {...props}
                        >
                          {code}
                        </SyntaxHighlighter>
                      </div>
                    );
                  }

                  return (
                    <code
                      className="bg-slate-200 dark:bg-slate-700 px-1 py-0.5 rounded text-sm font-mono"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                a({ children, href, ...props }: any) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                      {...props}
                    >
                      {children}
                    </a>
                  );
                },
                table({ children, ...props }: any) {
                  return (
                    <div className="overflow-x-auto my-3">
                      <table
                        className="border-collapse border border-border text-sm w-full"
                        {...props}
                      >
                        {children}
                      </table>
                    </div>
                  );
                },
                th({ children, ...props }: any) {
                  return (
                    <th
                      className="border border-border bg-muted px-3 py-2 font-semibold text-left"
                      {...props}
                    >
                      {children}
                    </th>
                  );
                },
                td({ children, ...props }: any) {
                  return (
                    <td className="border border-border px-3 py-2" {...props}>
                      {children}
                    </td>
                  );
                },
              }}
            >
              {message.content || "\u00A0"}
            </ReactMarkdown>

            {/* Citations */}
            {message.citations && message.citations.length > 0 && (
              <div className="mt-3 pt-2 border-t border-border/50 flex flex-wrap gap-1.5">
                {message.citations.map((cite) => (
                  <CitationBadge key={cite.index} citation={cite} />
                ))}
              </div>
            )}

            {/* Streaming indicator */}
            {message.isStreaming && (
              <div className="mt-2 flex items-center gap-1.5">
                <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                <span className="text-xs text-muted-foreground">
                  Generating response...
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-primary/50 text-primary-foreground rounded-br-md"
            : "bg-muted/50 rounded-bl-md"
        }`}
      >
        <div className="space-y-2 animate-pulse">
          <div className="h-3 bg-muted-foreground/20 rounded w-3/4" />
          <div className="h-3 bg-muted-foreground/20 rounded w-1/2" />
          <div className="h-3 bg-muted-foreground/20 rounded w-2/3" />
        </div>
      </div>
    </div>
  );
}
