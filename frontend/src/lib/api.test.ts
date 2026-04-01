import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { auth, chat, documents, profile, analytics } from './api';
import axios from 'axios';

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: vi.fn(),
      get: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
  },
}));

describe('API Module', () => {
  const mockApi = axios.create();

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Auth API', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        data: {
          access: 'fake-access-token',
          refresh: 'fake-refresh-token',
        },
      };
      mockApi.post.mockResolvedValueOnce(mockResponse);

      const result = await auth.login('testuser', 'password123');

      expect(mockApi.post).toHaveBeenCalledWith('/auth/token/', {
        username: 'testuser',
        password: 'password123',
      });
      expect(localStorage.getItem('access_token')).toBe('fake-access-token');
      expect(localStorage.getItem('refresh_token')).toBe('fake-refresh-token');
    });

    it('should register successfully', async () => {
      const mockResponse = {
        data: {
          message: 'User created successfully',
          user_id: 1,
          username: 'newuser',
        },
      };
      mockApi.post.mockResolvedValueOnce(mockResponse);

      const result = await auth.register('newuser', 'password123', 'test@example.com');

      expect(mockApi.post).toHaveBeenCalledWith('/auth/register/', {
        username: 'newuser',
        password: 'password123',
        email: 'test@example.com',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle forgot password', async () => {
      const mockResponse = {
        data: { message: 'Password reset email sent' },
      };
      mockApi.post.mockResolvedValueOnce(mockResponse);

      const result = await auth.forgotPassword('test@example.com');

      expect(mockApi.post).toHaveBeenCalledWith('/auth/forgot-password/', {
        email: 'test@example.com',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should logout and clear tokens', () => {
      localStorage.setItem('access_token', 'token');
      localStorage.setItem('refresh_token', 'refresh');

      auth.logout();

      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });

    it('should check authentication status', () => {
      expect(auth.isAuthenticated()).toBe(false);

      localStorage.setItem('access_token', 'some-token');

      expect(auth.isAuthenticated()).toBe(true);
    });
  });

  describe('Chat API', () => {
    it('should send message', async () => {
      const mockResponse = {
        data: {
          reply: 'Hello!',
          model_used: 'gemini',
          tools_used: [],
          intent: 'greeting',
        },
      };
      mockApi.post.mockResolvedValueOnce(mockResponse);

      const result = await chat.sendMessage('Hello', 'conv-123');

      expect(mockApi.post).toHaveBeenCalledWith('/chat/', {
        message: 'Hello',
        conversation_id: 'conv-123',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should get conversations', async () => {
      const mockResponse = {
        data: [
          { id: '1', title: 'Chat 1', updated_at: '2024-01-01' },
          { id: '2', title: 'Chat 2', updated_at: '2024-01-02' },
        ],
      };
      mockApi.get.mockResolvedValueOnce(mockResponse);

      const result = await chat.getConversations();

      expect(mockApi.get).toHaveBeenCalledWith('/conversations/');
      expect(result).toEqual(mockResponse.data);
    });

    it('should get conversation details', async () => {
      const mockResponse = {
        data: {
          id: '1',
          title: 'Chat 1',
          messages: [{ role: 'user', content: 'Hello' }],
        },
      };
      mockApi.get.mockResolvedValueOnce(mockResponse);

      const result = await chat.getConversation('1');

      expect(mockApi.get).toHaveBeenCalledWith('/conversations/1/');
      expect(result).toEqual(mockResponse.data);
    });

    it('should delete conversation', async () => {
      const mockResponse = { data: { success: true } };
      mockApi.delete.mockResolvedValueOnce(mockResponse);

      const result = await chat.deleteConversation('1');

      expect(mockApi.delete).toHaveBeenCalledWith('/conversations/1/delete/');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('Documents API', () => {
    it('should list documents', async () => {
      const mockResponse = {
        data: [{ id: '1', file: 'doc.pdf', status: 'processed' }],
      };
      mockApi.get.mockResolvedValueOnce(mockResponse);

      const result = await documents.list();

      expect(mockApi.get).toHaveBeenCalledWith('/documents/');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('Profile API', () => {
    it('should get profile', async () => {
      const mockResponse = {
        data: {
          business_name: 'Test Business',
          industry: 'Technology',
        },
      };
      mockApi.get.mockResolvedValueOnce(mockResponse);

      const result = await profile.get();

      expect(mockApi.get).toHaveBeenCalledWith('/profile/');
      expect(result).toEqual(mockResponse.data);
    });

    it('should update profile', async () => {
      const mockResponse = {
        data: {
          business_name: 'Updated Business',
          industry: 'AI',
        },
      };
      mockApi.post.mockResolvedValueOnce(mockResponse);

      const result = await profile.update({
        business_name: 'Updated Business',
        industry: 'AI',
      });

      expect(mockApi.post).toHaveBeenCalledWith('/profile/', {
        business_name: 'Updated Business',
        industry: 'AI',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('Analytics API', () => {
    it('should get analytics', async () => {
      const mockResponse = {
        data: {
          insights: {},
          followups: {},
        },
      };
      mockApi.get.mockResolvedValueOnce(mockResponse);

      const result = await analytics.get();

      expect(mockApi.get).toHaveBeenCalledWith('/analytics/');
      expect(result).toEqual(mockResponse.data);
    });
  });
});
