# Next.js 14 Frontend Integration Guide

Complete frontend for the Business Assistant Django backend.

## 1. Project Setup

```bash
npx create-next-app@latest business-assistant-frontend --typescript --tailwind --app
cd business-assistant-frontend
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card badge separator
npm install axios
```

## 2. Environment Variables (.env.local)

```
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## 3. CORS Configuration (Django)

Add to `config/settings/dev.py`:

```python
CORS_ALLOW_ALL_ORIGINS = True  # Dev only
# Or restrict to your frontend:
# CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
```

Install `django-cors-headers` if not already:
```bash
pip install django-cors-headers
```

Add to `INSTALLED_APPS` in `base.py`:
```python
"corsheaders",
```

Add to `MIDDLEWARE`:
```python
"corsheaders.middleware.CorsMiddleware",
```

## 4. API Client Setup

**lib/api.ts:**

```typescript
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          
          localStorage.setItem('access_token', response.data.access);
          originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
          
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, logout
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const auth = {
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/token/', { username, password });
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    return response.data;
  },
  
  register: async (username: string, password: string, email?: string) => {
    const response = await api.post('/auth/register/', { username, password, email });
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  
  isAuthenticated: () => !!localStorage.getItem('access_token'),
};

// Chat API
export const chat = {
  sendMessage: async (message: string, conversationId?: string) => {
    const response = await api.post('/chat/', {
      message,
      conversation_id: conversationId,
    });
    return response.data;
  },
  
  getConversations: async () => {
    const response = await api.get('/conversations/');
    return response.data;
  },
  
  getConversation: async (id: string) => {
    const response = await api.get(`/conversations/${id}/`);
    return response.data;
  },
};

// Documents API
export const documents = {
  upload: async (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/documents/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },
  
  list: async () => {
    const response = await api.get('/documents/');
    return response.data;
  },
};

// Profile API
export const profile = {
  get: async () => {
    const response = await api.get('/profile/');
    return response.data;
  },
  
  update: async (data: any) => {
    const response = await api.post('/profile/', data);
    return response.data;
  },
};
```

## 5. Authentication Components

**app/login/page.tsx:**

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { auth } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await auth.login(username, password);
      router.push('/chat');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Business Assistant</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Username</label>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

## 6. Chat Component

**app/chat/page.tsx:**

```typescript
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

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
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong.' },
      ]);
    } finally {
      setLoading(false);
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
          
          {loading && (
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
```

## 7. Document Upload Component

**components/document-upload.tsx:**

```typescript
'use client';

import { useState } from 'react';
import { documents } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

export default function DocumentUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedDocs, setUploadedDocs] = useState<any[]>([]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      const response = await documents.upload(file, setProgress);
      setUploadedDocs((prev) => [...prev, response]);
    } catch (err) {
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            disabled={uploading}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer flex flex-col items-center gap-2"
          >
            <div className="text-4xl">📄</div>
            <p className="text-sm text-gray-600">
              Click to upload PDF, DOCX, or TXT
            </p>
            <Button disabled={uploading} variant="outline">
              {uploading ? 'Uploading...' : 'Select File'}
            </Button>
          </label>
        </div>

        {uploading && (
          <div className="space-y-2">
            <Progress value={progress} />
            <p className="text-sm text-center text-gray-500">{progress}%</p>
          </div>
        )}

        {uploadedDocs.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium">Uploaded Documents</h4>
            {uploadedDocs.map((doc) => (
              <div key={doc.id} className="flex items-center gap-2 text-sm">
                <span className="text-green-500">✓</span>
                {doc.title} ({doc.status})
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

## 8. Business Profile Form

**components/profile-form.tsx:**

```typescript
'use client';

import { useState, useEffect } from 'react';
import { profile } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';

export default function ProfileForm() {
  const [formData, setFormData] = useState({
    company_name: '',
    industry: '',
    company_size: '',
    description: '',
    goals: '',
    key_metrics: '{}',
  });
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load existing profile
    profile.get().then((data) => {
      setFormData({
        ...data,
        key_metrics: JSON.stringify(data.key_metrics || {}, null, 2),
      });
    }).catch(() => {
      // No profile yet
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await profile.update({
        ...formData,
        key_metrics: JSON.parse(formData.key_metrics),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      alert('Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Business Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium">Company Name</label>
            <Input
              value={formData.company_name}
              onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Industry</label>
            <Input
              value={formData.industry}
              onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
              placeholder="e.g., SaaS, Retail, Consulting"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Company Size</label>
            <Input
              value={formData.company_size}
              onChange={(e) => setFormData({ ...formData, company_size: e.target.value })}
              placeholder="e.g., 10-50 employees"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Description</label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="What does your business do?"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Goals</label>
            <Textarea
              value={formData.goals}
              onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
              placeholder="What are your main business goals?"
            />
          </div>
          
          <div>
            <label className="text-sm font-medium">Key Metrics (JSON)</label>
            <Textarea
              value={formData.key_metrics}
              onChange={(e) => setFormData({ ...formData, key_metrics: e.target.value })}
              placeholder='{"monthly_revenue": 50000, "customer_count": 100}'
              className="font-mono text-sm"
            />
          </div>
          
          <Button type="submit" disabled={loading}>
            {loading ? 'Saving...' : saved ? 'Saved!' : 'Save Profile'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

## 9. Layout with Auth Guard

**app/layout.tsx:**

```typescript
import './globals.css';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Business Assistant',
  description: 'AI-powered business assistant',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

**components/auth-guard.tsx:**

```typescript
'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { auth } from '@/lib/api';

const publicPaths = ['/login', '/register'];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const isPublic = publicPaths.includes(pathname);
    const isAuth = auth.isAuthenticated();

    if (!isAuth && !isPublic) {
      router.push('/login');
    } else if (isAuth && isPublic) {
      router.push('/chat');
    }
  }, [pathname, router]);

  return <>{children}</>;
}
```

## 10. Run the Frontend

```bash
npm run dev
```

Open http://localhost:3000

## Features Summary

- ✅ JWT auth with auto-refresh
- ✅ Real-time chat with tool badges
- ✅ Document upload with progress
- ✅ Business profile management
- ✅ Responsive design with Tailwind + shadcn/ui
- ✅ TypeScript throughout
