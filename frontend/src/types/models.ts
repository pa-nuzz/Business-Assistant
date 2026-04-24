// Core data models

export interface User {
  id: number;
  username: string;
  email: string;
  is_staff?: boolean;
  is_superuser?: boolean;
  date_joined?: string;
  last_login?: string;
}

export interface BusinessProfile {
  id: number;
  user: number;
  business_name: string;
  industry: string;
  business_type: string;
  goals: Goal[];
  key_metrics: Metric[];
  created_at: string;
  updated_at: string;
}

export interface Goal {
  id: number;
  business_profile: number;
  title: string;
  description?: string;
  status: 'active' | 'completed' | 'archived';
  target_date?: string;
  created_at: string;
}

export interface Metric {
  id: number;
  business_profile: number;
  key: string;
  name: string;
  value: string;
  unit?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  user: number;
  title: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface Message {
  id: string;
  conversation: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface Document {
  id: string;
  user: number;
  title: string;
  file: string;
  file_type: 'pdf' | 'docx' | 'txt' | 'md';
  status: 'pending' | 'processing' | 'ready' | 'failed';
  summary?: string;
  created_at: string;
  deleted_at?: string;
}

export interface Task {
  id: string;
  user: number;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'done' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  due_date?: string;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  tags: string[];
}

export interface Notification {
  id: number;
  user: number;
  message: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  is_read: boolean;
  action_url?: string;
  created_at: string;
}

export interface Tag {
  id: string;
  name: string;
  color?: string;
}
