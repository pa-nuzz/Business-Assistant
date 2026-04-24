'use client';

import { useState, useEffect, useCallback } from 'react';
import { Bell, X, Check, ArrowRight, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { notifications, auth } from '@/lib/api';
import { AxiosApiError } from '@/types/errors';
import { toast } from 'sonner';

interface Notification {
  id: number;
  message: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  created_at: string;
  is_read: boolean;
  action_url?: string;
}

interface FloatingNotificationWidgetProps {
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
}

export function FloatingNotificationWidget({ 
  position = 'bottom-right' 
}: FloatingNotificationWidgetProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [notificationsList, setNotificationsList] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [markingRead, setMarkingRead] = useState<number | null>(null);
  const [showBadge, setShowBadge] = useState(true);

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6',
  };

  const fetchNotifications = useCallback(async () => {
    // Only fetch if user is authenticated (has access token)
    if (!auth.isAuthenticated()) return;
    
    try {
      const data = await notifications.list();
      if (data && data.notifications) {
        setNotificationsList(data.notifications);
        setUnreadCount(data.count || 0);
      }
    } catch (err: unknown) {
      // Silently ignore auth errors (user not logged in)
      if ((err as AxiosApiError).response?.status === 401) return;
      // eslint-disable-next-line no-console
      console.error('Failed to fetch notifications:', err);
    }
  }, []);

  // Fetch on mount and periodically
  useEffect(() => {
    fetchNotifications();
    
    const interval = setInterval(fetchNotifications, 30000);
    
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchNotifications();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchNotifications]);

  // Listen for refresh event
  useEffect(() => {
    const handleRefresh = () => {
      fetchNotifications();
    };
    window.addEventListener('refresh-notifications', handleRefresh);
    return () => window.removeEventListener('refresh-notifications', handleRefresh);
  }, [fetchNotifications]);

  const handleMarkAsRead = async (e: React.MouseEvent, notificationId: number) => {
    e.stopPropagation();
    setMarkingRead(notificationId);
    
    try {
      await notifications.markAsRead(notificationId);
      
      setNotificationsList(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
      
      toast.success('Marked as read');
    } catch (err) {
      toast.error('Failed to mark as read');
    } finally {
      setMarkingRead(null);
    }
  };

  const handleMarkAllAsRead = async () => {
    setIsLoading(true);
    
    try {
      const unreadNotifications = notificationsList.filter(n => !n.is_read);
      await Promise.all(
        unreadNotifications.map(n => notifications.markAsRead(n.id))
      );
      
      setNotificationsList(prev => 
        prev.map(n => ({ ...n, is_read: true }))
      );
      setUnreadCount(0);
      
      toast.success('All notifications marked as read');
    } catch (err) {
      toast.error('Failed to mark all as read');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDismissBadge = () => {
    setShowBadge(false);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'normal': return 'bg-blue-500';
      case 'low': return 'bg-gray-400';
      default: return 'bg-blue-500';
    }
  };

  const getPriorityBg = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-50 border-red-100';
      case 'high': return 'bg-orange-50 border-orange-100';
      case 'normal': return 'bg-blue-50 border-blue-100';
      case 'low': return 'bg-gray-50 border-gray-100';
      default: return 'bg-blue-50 border-blue-100';
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

  const unreadNotifications = notificationsList.filter(n => !n.is_read);

  return (
    <div className={`fixed ${positionClasses[position]} z-50`}>
      <AnimatePresence mode="wait">
        {!isExpanded ? (
          // Collapsed State - Floating Bell Button
          <motion.div
            key="collapsed"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          >
            {/* Notification Preview Badge (shows for urgent/high priority) */}
            {showBadge && unreadNotifications.length > 0 && unreadNotifications[0].priority !== 'low' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute bottom-full right-0 mb-2 w-[280px]"
              >
                <div 
                  className={`p-3 rounded-xl border shadow-lg ${getPriorityBg(unreadNotifications[0].priority)} cursor-pointer`}
                  onClick={() => setIsExpanded(true)}
                >
                  <div className="flex items-start gap-2">
                    <div className={`w-2 h-2 rounded-full mt-1.5 ${getPriorityColor(unreadNotifications[0].priority)}`} />
                    <p className="text-sm text-slate-900 flex-1 line-clamp-2">
                      {unreadNotifications[0].message}
                    </p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDismissBadge();
                      }}
                      className="p-1 hover:bg-black/5 rounded transition-colors"
                    >
                      <X className="w-3 h-3 text-slate-400" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-slate-500">
                      {formatTime(unreadNotifications[0].created_at)}
                    </span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                  </div>
                </div>
              </motion.div>
            )}

            {/* Main Floating Button */}
            <button
              onClick={() => setIsExpanded(true)}
              className="relative group flex items-center justify-center w-14 h-14 bg-card border border-border rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all"
            >
              <Bell className="w-6 h-6 text-slate-900 group-hover:text-blue-600 transition-colors" />
              
              {/* Unread Count Badge */}
              {unreadCount > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 min-w-[20px] h-[20px] flex items-center justify-center bg-red-500 text-white text-xs font-bold rounded-full px-1 shadow-sm"
                >
                  {unreadCount > 99 ? '99+' : unreadCount}
                </motion.span>
              )}

              {/* Pulse animation for urgent notifications */}
              {unreadNotifications.some(n => n.priority === 'urgent') && (
                <span className="absolute inset-0 rounded-full bg-red-400 opacity-20 animate-ping" />
              )}
            </button>
          </motion.div>
        ) : (
          // Expanded State - Full Widget
          <motion.div
            key="expanded"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="w-[360px] bg-card rounded-2xl border border-border shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/50">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Bell className="w-5 h-5 text-slate-900" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center text-[8px] text-white font-bold">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </div>
                <h3 className="font-semibold text-sm">Notifications</h3>
              </div>
              
              <div className="flex items-center gap-1">
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllAsRead}
                    disabled={isLoading}
                    className="text-xs text-blue-600 hover:text-blue-700 px-2 py-1 rounded hover:bg-blue-50 transition-colors disabled:opacity-50"
                  >
                    {isLoading ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      'Mark all'
                    )}
                  </button>
                )}
                <button
                  onClick={() => setIsExpanded(false)}
                  className="p-1.5 hover:bg-muted rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>
            </div>

            {/* Notifications List */}
            <div className="max-h-[400px] overflow-y-auto">
              {notificationsList.length === 0 ? (
                <div className="px-4 py-12 text-center">
                  <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-3">
                    <Bell className="w-8 h-8 text-slate-400/50" />
                  </div>
                  <p className="text-sm text-slate-600">No notifications yet</p>
                  <p className="text-xs text-slate-500/60 mt-1">
                    We'll notify you of important updates
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {notificationsList.map((notification, index) => (
                    <motion.div
                      key={notification.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`relative p-4 hover:bg-muted/50 transition-colors ${
                        !notification.is_read ? getPriorityBg(notification.priority) : ''
                      }`}
                    >
                      {/* Priority indicator */}
                      <div className={`absolute left-0 top-0 bottom-0 w-1 ${getPriorityColor(notification.priority)}`} />
                      
                      <div className="pl-3">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm text-slate-900 flex-1">
                            {notification.message}
                          </p>
                          
                          {!notification.is_read && (
                            <button
                              onClick={(e) => handleMarkAsRead(e, notification.id)}
                              disabled={markingRead === notification.id}
                              className="flex-shrink-0 p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50"
                              title="Mark as read"
                            >
                              {markingRead === notification.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Check className="w-4 h-4" />
                              )}
                            </button>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-slate-500">
                            {formatTime(notification.created_at)}
                          </span>
                          
                          {notification.priority !== 'normal' && (
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                              notification.priority === 'urgent' 
                                ? 'bg-red-100 text-red-700' 
                                : notification.priority === 'high'
                                ? 'bg-orange-100 text-orange-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}>
                              {notification.priority}
                            </span>
                          )}
                        </div>
                        
                        {/* Action URL */}
                        {notification.action_url && (
                          <a
                            href={notification.action_url}
                            className="inline-flex items-center gap-1 mt-2 text-xs text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            View details
                            <ArrowRight className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            {notificationsList.length > 0 && (
              <div className="px-4 py-3 border-t border-border bg-muted/30">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">
                    {unreadCount} of {notificationsList.length} unread
                  </span>
                  <a 
                    href="/notifications" 
                    className="text-xs text-blue-600 hover:text-blue-700 hover:underline"
                  >
                    View all
                  </a>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
