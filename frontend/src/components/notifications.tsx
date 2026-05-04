"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Bell, Check, CheckCheck, X, User, FileText, 
  Clock, AlertCircle, MessageSquare, Trash
} from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";
import { toast } from "sonner";

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  task_id?: string;
  document_id?: string;
  actor?: string;
}

export function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await api.get('/notifications/');
      setNotifications(response.data.notifications);
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      // Silently fail - notifications are not critical
    }
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await api.get('/notifications/unread-count/');
      setUnreadCount(response.data.count);
    } catch (error) {
      // Silently fail
    }
  }, []);

  const markAsRead = async (notificationId: string) => {
    try {
      await api.post(`/notifications/${notificationId}/read/`);
      fetchNotifications();
    } catch (error) {
      toast.error('Failed to mark as read');
    }
  };

  const markAllRead = async () => {
    try {
      await api.post('/notifications/mark-all-read/');
      fetchNotifications();
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  // WebSocket connection for real-time notifications
  useEffect(() => {
    const connectWebSocket = () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/notifications/`;
      const socket = new WebSocket(`${wsUrl}?token=${token}`);

      socket.onopen = () => {
        console.log('Notification WebSocket connected');
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          // Add new notification
          setNotifications(prev => [data, ...prev]);
          setUnreadCount(prev => prev + 1);
          
          // Show toast for new notification
          toast.info(data.title, {
            description: data.message,
            duration: 5000,
          });
        }
      };

      socket.onclose = () => {
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      setWs(socket);
    };

    connectWebSocket();
    fetchNotifications();

    // Poll for unread count every 30 seconds as fallback
    const interval = setInterval(fetchUnreadCount, 30000);

    return () => {
      ws?.close();
      clearInterval(interval);
    };
  }, [fetchNotifications, fetchUnreadCount]);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'task_assigned': return <User className="h-4 w-4 text-blue-500" />;
      case 'task_mentioned': return <MessageSquare className="h-4 w-4 text-purple-500" />;
      case 'due_date_approaching': return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'due_date_overdue': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'document_shared': return <FileText className="h-4 w-4 text-green-500" />;
      default: return <Bell className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute right-0 top-full mt-2 w-80 bg-background border rounded-lg shadow-lg z-50"
          >
            <div className="flex items-center justify-between p-3 border-b">
              <h3 className="font-medium">Notifications</h3>
              <div className="flex items-center gap-1">
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 text-xs"
                    onClick={markAllRead}
                  >
                    <CheckCheck className="h-3 w-3 mr-1" />
                    Mark all read
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setIsOpen(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No notifications
                </p>
              ) : (
                <div className="divide-y">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-3 flex items-start gap-3 hover:bg-muted/50 transition-colors ${
                        !notification.is_read ? 'bg-blue-50/50' : ''
                      }`}
                    >
                      <div className="mt-0.5">
                        {getNotificationIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${!notification.is_read ? 'font-medium' : ''}`}>
                          {notification.title}
                        </p>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {notification.message}
                        </p>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-xs text-muted-foreground">
                            {formatTime(notification.created_at)}
                          </span>
                          {!notification.is_read && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => markAsRead(notification.id)}
                            >
                              <Check className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
