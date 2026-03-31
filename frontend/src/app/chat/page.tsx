'use client';

import { useState, useRef, useEffect } from 'react';
import { chat } from '@/lib/api';
import { ArrowUp, Loader2 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  model_used?: string;
  tools_used?: string[];
  intent?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>();
  const [streamingContent, setStreamingContent] = useState('');
  const [currentIntent, setCurrentIntent] = useState<string>('');
  const [currentTools, setCurrentTools] = useState<string[]>([]);
  const [currentModel, setCurrentModel] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Fix for streaming bug - use refs for accumulators
  const streamAccumRef = useRef('');
  const modelUsedRef = useRef('');
  const toolsUsedRef = useRef<string[]>([]);
  const intentRef = useRef('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);
    setStreamingContent('');
    setCurrentIntent('');
    setCurrentTools([]);
    setCurrentModel('');
    
    // Reset refs
    streamAccumRef.current = '';
    modelUsedRef.current = '';
    toolsUsedRef.current = [];
    intentRef.current = '';

    try {
      await chat.sendMessageStream(
        userMessage,
        conversationId,
        (token) => {
          // Fix: accumulate in ref, not state
          streamAccumRef.current += token;
          setStreamingContent(streamAccumRef.current);
        },
        (metadata) => {
          modelUsedRef.current = metadata.model || '';
          toolsUsedRef.current = metadata.tools_used || [];
          intentRef.current = metadata.intent || '';
          setCurrentModel(metadata.model || '');
          setCurrentTools(metadata.tools_used || []);
          setCurrentIntent(metadata.intent || '');
        },
        () => {
          // Stream complete - use ref value
          const finalText = streamAccumRef.current;
          streamAccumRef.current = '';
          setStreamingContent('');
          setMessages((prev) => [...prev, {
            role: 'assistant',
            content: finalText,
            model_used: modelUsedRef.current,
            tools_used: toolsUsedRef.current,
            intent: intentRef.current,
          }]);
          setLoading(false);
        },
        (error) => {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: `Error: ${error}` },
          ]);
          setStreamingContent('');
          setLoading(false);
        }
      );
    } catch (err) {
      // Fallback to non-streaming
      try {
        const response = await chat.sendMessage(userMessage, conversationId);
        
        if (!conversationId) {
          setConversationId(response.conversation_id);
        }

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.reply,
            model_used: response.model_used,
            tools_used: response.tools_used,
            intent: response.intent,
          },
        ]);
      } catch (fallbackErr) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
        ]);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit();
    }
  };

  return (
    <div 
      style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100vh',
        backgroundColor: 'var(--surface-0)',
      }}
    >
      {/* Header */}
      <header 
        style={{ 
          height: '48px', 
          borderBottom: '1px solid var(--surface-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h1 
            style={{ 
              fontSize: '15px', 
              fontWeight: 500, 
              color: 'var(--ink-0)',
              margin: 0,
            }}
          >
            {conversationId ? 'Conversation' : 'New Chat'}
          </h1>
          {currentModel && (
            <span 
              style={{ 
                fontSize: '11px', 
                padding: '2px 8px', 
                backgroundColor: 'var(--surface-2)',
                color: 'var(--ink-2)',
                borderRadius: '4px',
              }}
            >
              {currentModel}
            </span>
          )}
          {currentIntent && (
            <span 
              style={{ 
                fontSize: '11px', 
                padding: '2px 8px', 
                backgroundColor: 'var(--accent-blue-subtle)',
                color: 'var(--accent-blue)',
                borderRadius: '4px',
                textTransform: 'capitalize',
              }}
            >
              {currentIntent}
            </span>
          )}
        </div>
        <button
          onClick={() => {
            setMessages([]);
            setConversationId(undefined);
            setCurrentIntent('');
            setCurrentTools([]);
            setCurrentModel('');
          }}
          style={{
            fontSize: '13px',
            color: 'var(--ink-2)',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '6px 12px',
            borderRadius: '6px',
            transition: 'background-color 120ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--surface-1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          New Chat
        </button>
      </header>

      {/* Messages Area */}
      <div 
        style={{ 
          flex: 1, 
          overflowY: 'auto',
          padding: '24px',
        }}
      >
        <div style={{ maxWidth: '720px', margin: '0 auto' }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: '120px' }}>
              <p 
                style={{ 
                  fontSize: '16px', 
                  color: 'var(--ink-2)',
                  margin: 0,
                }}
              >
                How can I help with your business today?
              </p>
            </div>
          )}
          
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: '16px',
              }}
            >
              <div
                style={{
                  maxWidth: msg.role === 'user' ? '75%' : '85%',
                  padding: msg.role === 'user' ? '10px 14px' : '12px 16px',
                  backgroundColor: msg.role === 'user' ? 'var(--accent-blue)' : 'var(--surface-1)',
                  color: msg.role === 'user' ? '#fff' : 'var(--ink-0)',
                  borderRadius: msg.role === 'user' 
                    ? '16px 16px 4px 16px' 
                    : '4px 16px 16px 16px',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--surface-border)',
                  fontSize: '14px',
                  lineHeight: 1.6,
                  boxShadow: msg.role === 'user' ? 'none' : '0 1px 3px rgba(0,0,0,0.06)',
                }}
              >
                <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                
                {msg.role === 'assistant' && (msg.tools_used?.length || msg.model_used) && (
                  <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {msg.tools_used?.map((tool) => (
                      <span
                        key={tool}
                        style={{
                          fontSize: '11px',
                          padding: '2px 6px',
                          backgroundColor: 'var(--surface-2)',
                          color: 'var(--ink-2)',
                          borderRadius: '4px',
                        }}
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {streamingContent && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}>
              <div
                style={{
                  maxWidth: '85%',
                  padding: '12px 16px',
                  backgroundColor: 'var(--surface-1)',
                  color: 'var(--ink-0)',
                  borderRadius: '4px 16px 16px 16px',
                  border: '1px solid var(--surface-border)',
                  fontSize: '14px',
                  lineHeight: 1.6,
                  boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                }}
              >
                <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{streamingContent}</p>
              </div>
            </div>
          )}
          
          {loading && !streamingContent && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}>
              <div
                style={{
                  padding: '16px 20px',
                  backgroundColor: 'var(--surface-1)',
                  borderRadius: '4px 16px 16px 16px',
                  border: '1px solid var(--surface-border)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="animate-pulse-slow"
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--ink-3)',
                        animationDelay: `${i * 0.15}s`,
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div 
        style={{ 
          borderTop: '1px solid var(--surface-border)',
          padding: '16px 24px',
        }}
      >
        <div style={{ maxWidth: '720px', margin: '0 auto' }}>
          <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your business..."
              disabled={loading}
              rows={1}
              style={{
                width: '100%',
                minHeight: '44px',
                maxHeight: '120px',
                padding: '10px 44px 10px 14px',
                fontSize: '14px',
                color: 'var(--ink-0)',
                backgroundColor: 'var(--surface-0)',
                border: '1px solid var(--surface-border-strong)',
                borderRadius: 'var(--r-lg)',
                outline: 'none',
                resize: 'none',
                transition: 'border-color 120ms ease, box-shadow 120ms ease',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-blue)';
                e.currentTarget.style.boxShadow = '0 0 0 2px var(--accent-blue-subtle)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--surface-border-strong)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              style={{
                position: 'absolute',
                right: '6px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: loading || !input.trim() ? 'var(--surface-2)' : 'var(--accent-blue)',
                border: 'none',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: loading || !input.trim() ? 'var(--ink-3)' : '#fff',
                transition: 'background-color 120ms ease',
              }}
            >
              {loading ? (
                <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
              ) : (
                <ArrowUp size={16} />
              )}
            </button>
          </form>
          <p 
            style={{ 
              fontSize: '12px', 
              color: 'var(--ink-3)', 
              margin: '8px 0 0',
              textAlign: 'center',
            }}
          >
            Cmd+Enter to send
          </p>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
