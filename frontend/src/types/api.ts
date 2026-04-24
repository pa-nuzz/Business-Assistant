// API request/response types

import { User, Conversation, Message, Document, Task, Notification, BusinessProfile } from './models';

// Auth
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  user: User;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
}

export interface VerifyEmailRequest {
  username: string;
  code: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  email: string;
  code: string;
  new_password: string;
}

// Chat
export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  title?: string;
}

export interface ChatStreamToken {
  type: 'token';
  content: string;
}

export interface ChatStreamMetadata {
  type: 'metadata';
  conversation_id: string;
  title?: string;
}

export interface ChatStreamDone {
  type: 'done';
}

export interface ChatStreamError {
  type: 'error';
  error: string;
}

export type ChatStreamEvent = ChatStreamToken | ChatStreamMetadata | ChatStreamDone | ChatStreamError;

// Conversations
export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export interface ConversationDetailResponse {
  id: string;
  title: string;
  messages: Message[];
}

// Documents
export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentUploadResponse {
  id: string;
  title: string;
  status: string;
  message: string;
}

export interface DocumentStatusResponse {
  id: string;
  status: string;
  summary?: string;
}

export interface DocumentSummaryResponse {
  id: string;
  summary: string;
}

// Tasks
export interface TaskListResponse {
  tasks: Task[];
  total: number;
  page: number;
  page_size: number;
}

export interface TaskCreateRequest {
  title: string;
  description?: string;
  priority?: string;
  due_date?: string;
}

export interface TaskUpdateRequest {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
}

// Notifications
export interface NotificationListResponse {
  notifications: Notification[];
  count: number;
}

// User Profile
export type UserInfoResponse = User;

export interface UsernameUpdateRequest {
  username: string;
}

export interface PasswordUpdateRequest {
  current_password: string;
  new_password: string;
}

// Business Profile
export type BusinessProfileResponse = BusinessProfile;

export interface BusinessProfileUpdateRequest {
  business_name?: string;
  industry?: string;
  business_type?: string;
}

// Analytics
export interface BusinessAnalyticsResponse {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  documents_uploaded: number;
  conversations_count: number;
  goals_progress: number;
}

// Admin
export interface AdminDashboardResponse {
  users: {
    total: number;
    active_today: number;
    active_this_week: number;
    new_this_week: number;
  };
  conversations: {
    total: number;
    created_today: number;
    messages_today: number;
  };
  documents: {
    total: number;
    pending: number;
    ready: number;
    failed: number;
  };
  tasks: {
    total: number;
    completed: number;
    in_progress: number;
    todo: number;
  };
  generated_at: string;
}

export interface AdminBroadcastRequest {
  message: string;
  type: 'info' | 'warning' | 'maintenance';
}

// Errors
export interface ApiError {
  error: string;
  detail?: string;
  code?: string;
}
