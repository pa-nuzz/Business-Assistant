import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// Event emitter for auth failures (components should listen and use Next.js router)
const authErrorListeners: Set<() => void> = new Set();

export const onAuthError = (callback: () => void) => {
  authErrorListeners.add(callback);
  return () => authErrorListeners.delete(callback);
};

const triggerAuthRedirect = () => {
  authErrorListeners.forEach(cb => cb());
  // Fallback if no listeners registered
  if (authErrorListeners.size === 0 && typeof window !== 'undefined') {
    window.location.href = '/login';
  }
};

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout for all requests
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle token refresh on 401 and network errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle network errors
    if (!error.response) {
      // Network error - backend not reachable
      if (error.code === 'ECONNABORTED' || error.message?.includes('Network Error')) {
        // Log to monitoring service instead of console
        // console.error is prohibited in production code
      }
      return Promise.reject(new Error('Network error: Backend server not reachable. Please ensure the server is running.'));
    }
    
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
          triggerAuthRedirect();
          return Promise.reject(refreshError);
        }
      }
    }
    
    // Handle 401 without refresh token or after refresh failed
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      triggerAuthRedirect();
    }
    
    return Promise.reject(error);
  }
);

export default api;

// Auth API - Premium Auth System with Email Verification
export const auth = {
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/login/', { username, password });
    if (response.data.access) {
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    return response.data;
  },
  
  register: async (username: string, password: string, email: string) => {
    const response = await api.post('/auth/register/', { username, password, email });
    return response.data;
  },
  
  verifyEmail: async (username: string, code: string) => {
    const response = await api.post('/auth/verify-email/', { username, code });
    if (response.data.access) {
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
    }
    return response.data;
  },
  
  resendVerification: async (username: string) => {
    const response = await api.post('/auth/resend-verification/', { username });
    return response.data;
  },
  
  forgotPassword: async (email: string) => {
    const response = await api.post('/auth/forgot-password/', { email });
    return response.data;
  },
  
  verifyResetCode: async (email: string, code: string) => {
    const response = await api.post('/auth/verify-reset-code/', { email, code });
    return response.data;
  },
  
  resetPassword: async (email: string, code: string, newPassword: string) => {
    const response = await api.post('/auth/reset-password/', { email, code, new_password: newPassword });
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
  
  getConversations: async (page = 1, pageSize = 20) => {
    const params = new URLSearchParams();
    params.append('page', String(page));
    params.append('page_size', String(pageSize));
    const response = await api.get(`/conversations/?${params.toString()}`);
    return response.data;
  },
  
  getConversation: async (id: string) => {
    const response = await api.get(`/conversations/${id}/`);
    return response.data;
  },

  deleteConversation: async (id: string) => {
    const response = await api.delete(`/conversations/${id}/delete/`);
    return response.data;
  },
};

// Documents API
export const documents = {
  upload: async (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/documents/upload/', formData, {
      headers: {
        // Must delete Content-Type to let browser set multipart boundary automatically
        'Content-Type': undefined,
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },
  
  list: async (page = 1, pageSize = 20) => {
    const params = new URLSearchParams();
    params.append('page', String(page));
    params.append('page_size', String(pageSize));
    const response = await api.get(`/documents/?${params.toString()}`);
    return response.data;
  },
  
  getSummary: async (docId: string) => {
    const response = await api.get(`/documents/${docId}/summary/`);
    return response.data;
  },
  
  search: async (docId: string, query: string) => {
    const response = await api.post('/chat/', {
      message: `Search in document for: ${query}`,
      doc_id: docId,
    });
    return response.data;
  },
};

// Profile API
export interface ProfileData {
  company_name?: string;
  industry?: string;
  company_size?: string;
  description?: string;
  goals?: string[];
  key_metrics?: Record<string, number>;
  [key: string]: string | string[] | Record<string, number> | undefined;
}

export const profile = {
  get: async () => {
    const response = await api.get('/profile/');
    return response.data;
  },
  
  update: async (data: ProfileData) => {
    const response = await api.post('/profile/', data);
    return response.data;
  },
  
  updateWithAvatar: async (data: ProfileData, avatarFile: File) => {
    const formData = new FormData();
    
    // Add all data fields
    Object.keys(data).forEach(key => {
      if (data[key] !== undefined && data[key] !== null) {
        formData.append(key, typeof data[key] === 'object' ? JSON.stringify(data[key]) : data[key]);
      }
    });
    
    // Add avatar file
    formData.append('avatar', avatarFile);
    
    const response = await api.post('/profile/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// User API
export const user = {
  getInfo: async () => {
    const response = await api.get('/user/info/');
    return response.data;
  },
  
  updateUsername: async (username: string) => {
    const response = await api.post('/user/update-username/', { username });
    return response.data;
  },
  
  updatePassword: async (currentPassword: string, newPassword: string) => {
    const response = await api.post('/user/update-password/', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

// Analytics API
export const analytics = {
  get: async () => {
    const response = await api.get('/analytics/');
    return response.data;
  },
};

// Tasks API
export const tasks = {
  list: async (filters?: { status?: string; priority?: string; search?: string }, page = 1, pageSize = 20) => {
    const params = new URLSearchParams();
    params.append('page', String(page));
    params.append('page_size', String(pageSize));
    if (filters?.status) params.append('status', filters.status);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.search) params.append('search', filters.search);
    const response = await api.get(`/tasks/?${params.toString()}`);
    return response.data;
  },
  
  create: async (data: {
    title: string;
    description?: string;
    priority?: string;
    status?: string;
    due_date?: string;
    assignee_id?: number;
    tags?: string[];
    document_ids?: string[];
  }) => {
    const response = await api.post('/tasks/create/', data);
    return response.data;
  },
  
  get: async (id: string) => {
    const response = await api.get(`/tasks/${id}/`);
    return response.data;
  },
  
  update: async (id: string, data: Partial<{ title: string; description?: string; priority?: string; status?: string; due_date?: string; assignee_id?: number; tags?: string[]; document_ids?: string[] }>) => {
    const response = await api.put(`/tasks/${id}/update/`, data);
    return response.data;
  },
  
  delete: async (id: string) => {
    const response = await api.delete(`/tasks/${id}/delete/`);
    return response.data;
  },
  
  complete: async (id: string, data?: { completion_notes?: string; actual_hours?: number }) => {
    const response = await api.post(`/tasks/${id}/complete/`, data || {});
    return response.data;
  },
  
  reopen: async (id: string) => {
    const response = await api.post(`/tasks/${id}/reopen/`);
    return response.data;
  },
  
  getDashboard: async () => {
    const response = await api.get('/tasks/dashboard/');
    return response.data;
  },
  
  getStats: async () => {
    const response = await api.get('/tasks/stats/');
    return response.data;
  },
  
  listComments: async (taskId: string) => {
    const response = await api.get(`/tasks/${taskId}/comments/`);
    return response.data;
  },
  
  addComment: async (taskId: string, content: string) => {
    const response = await api.post(`/tasks/${taskId}/comments/create/`, { content });
    return response.data;
  },
  
  deleteComment: async (taskId: string, commentId: string) => {
    const response = await api.delete(`/tasks/${taskId}/comments/${commentId}/delete/`);
    return response.data;
  },
  
  // AI Task Extraction
  extractFromText: async (text: string, conversationId?: string) => {
    const response = await api.post('/tasks/extract/', { text, conversation_id: conversationId });
    return response.data;
  },
  
  acceptSuggestion: async (suggestionId: string) => {
    const response = await api.post(`/tasks/suggestions/${suggestionId}/accept/`);
    return response.data;
  },
  
  rejectSuggestion: async (suggestionId: string) => {
    const response = await api.post(`/tasks/suggestions/${suggestionId}/reject/`);
    return response.data;
  },
};

// Onboarding API
export const onboarding = {
  getStatus: async () => {
    const response = await api.get('/onboarding/status/');
    return response.data;
  },
  seedDemo: async () => {
    const response = await api.post('/demo/seed/');
    return response.data;
  },
};

// Notifications API
export const notifications = {
  list: async () => {
    const response = await api.get('/notifications/');
    return response.data;
  },
  markAsRead: async (notificationId: number) => {
    const response = await api.post(`/notifications/${notificationId}/read/`);
    return response.data;
  },
};
