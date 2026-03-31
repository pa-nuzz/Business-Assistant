'use client';

import { useState, useRef, useEffect } from 'react';
import { chat } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  model_used?: string;
  tools_used?: string[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>();
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);
    setStreamingContent('');

    let modelUsed = '';
    let toolsUsed: string[] = [];

    try {
      await chat.sendMessageStream(
        userMessage,
        conversationId,
        (token) => {
          setStreamingContent((prev) => prev + token);
        },
        (metadata) => {
          modelUsed = metadata.model;
          toolsUsed = metadata.tools_used || [];
          if (!conversationId) {
            // Note: conversation_id isn't returned in stream, we'd need to track it differently
          }
        },
        () => {
          // Stream complete
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: streamingContent || 'No response received.',
              model_used: modelUsed,
              tools_used: toolsUsed,
            },
          ]);
          setStreamingContent('');
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
          },
        ]);
      } catch (fallbackErr) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'Sorry, something went wrong.' },
        ]);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <h1 className="text-xl font-semibold">Business Assistant</h1>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => {
              setMessages([]);
              setConversationId(undefined);
            }}>
              New Chat
            </Button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-lg">How can I help with your business today?</p>
            </div>
          )}
          
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <Card className={`max-w-[80%] ${msg.role === 'user' ? 'bg-blue-50' : 'bg-white'}`}>
                <CardContent className="p-4">
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  
                  {msg.role === 'assistant' && (msg.tools_used?.length || msg.model_used) && (
                    <>
                      <Separator className="my-3" />
                      <div className="flex flex-wrap gap-2 items-center text-xs text-gray-500">
                        {msg.model_used && (
                          <Badge variant="secondary">Model: {msg.model_used}</Badge>
                        )}
                        {msg.tools_used?.map((tool) => (
                          <Badge key={tool} variant="outline" className="text-green-600">
                            {tool}
                          </Badge>
                        ))}
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </div>
          ))}
          
          {streamingContent && (
            <div className="flex justify-start">
              <Card className="bg-white">
                <CardContent className="p-4">
                  <p className="whitespace-pre-wrap">{streamingContent}</p>
                </CardContent>
              </Card>
            </div>
          )}
          
          {loading && !streamingContent && (
            <div className="flex justify-start">
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-gray-500">
                    <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
                    Thinking...
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your business..."
            className="flex-1"
            disabled={loading}
          />
          <Button type="submit" disabled={loading || !input.trim()}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
