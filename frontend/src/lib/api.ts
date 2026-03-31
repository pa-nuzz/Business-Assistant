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
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
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
  
  isAuthenticated: () => {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('access_token');
  },
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

  sendMessageStream: async (
    message: string,
    conversationId: string | undefined,
    onToken: (token: string) => void,
    onMetadata: (metadata: any) => void,
    onDone: () => void,
    onError: (error: string) => void
  ) => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/chat/stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      onError(error);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError('No response body');
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              onDone();
              return;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.token) {
                onToken(parsed.token);
              } else if (parsed.metadata) {
                onMetadata(parsed.metadata);
              } else if (parsed.error) {
                onError(parsed.error);
                return;
              }
            } catch {
              // Ignore parse errors for non-JSON data
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
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
