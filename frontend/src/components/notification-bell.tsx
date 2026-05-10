'use client';

import { useState, useEffect, useCallback } from 'react';
import { Bell, Check, X, Loader2, Sparkles, AlertCircle, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { notifications, auth } from '@/lib/api';
import { toast } from 'sonner';

interface Notification {
  id: number;
  message: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  created_at: string;
  is_read: boolean;
  action_url?: string;
}

interface NotificationBellProps {
  className?: string;
}

export function NotificationBell({ className }: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notificationsList, setNotificationsList] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [markingRead, setMarkingRead] = useState<number | null>(null);

  const fetchNotifications = useCallback(async () => {
    if (!auth.isAuthenticated()) return;
    
    try {
      const data = await notifications.list();
      if (data && data.notifications) {
        setNotificationsList(data.notifications);
        setUnreadCount(data.count || 0);
      }
    } catch (_err: unknown) {
      const error = _err as { response?: { status?: number } };
      if (error?.response?.status === 401) return;
      console.error('Failed to fetch notifications:', _err);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') fetchNotifications();
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchNotifications]);

  useEffect(() => {
    const handleRefresh = () => fetchNotifications();
    window.addEventListener('refresh-notifications', handleRefresh);
    return () => window.removeEventListener('refresh-notifications', handleRefresh);
  }, [fetchNotifications]);

  const handleMarkAsRead = async (e: React.MouseEvent, notificationId: number) => {
    e.stopPropagation();
    setMarkingRead(notificationId);
    
    try {
      await notifications.markAsRead(notificationId);
      setNotificationsList(prev => prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
      toast.success('Marked as read');
    } catch {
      toast.error('Failed to mark as read');
    } finally {
      setMarkingRead(null);
    }
  };

  const handleMarkAllAsRead = async () => {
    setIsLoading(true);
    try {
      const unreadNotifications = notificationsList.filter(n => !n.is_read);
      await Promise.all(unreadNotifications.map(n => notifications.markAsRead(n.id)));
      
      setNotificationsList(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch {
      toast.error('Failed to mark all as read');
    } finally {
      setIsLoading(false);
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent': return <AlertCircle className="w-4 h-4 text-rose-500" />;
      case 'high': return <Sparkles className="w-4 h-4 text-orange-500" />;
      case 'normal': return <Info className="w-4 h-4 text-indigo-500" />;
      default: return <Info className="w-4 h-4 text-slate-400" />;
    }
  };

  const getPriorityBg = (priority: string, isRead: boolean) => {
    if (isRead) return 'bg-white/40 border-white/20 hover:bg-white/60';
    switch (priority) {
      case 'urgent': return 'bg-rose-50/80 border-rose-100 shadow-sm hover:bg-rose-50';
      case 'high': return 'bg-orange-50/80 border-orange-100 shadow-sm hover:bg-orange-50';
      default: return 'bg-indigo-50/80 border-indigo-100 shadow-sm hover:bg-indigo-50';
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
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2.5 rounded-xl bg-white/70 backdrop-blur-xl border border-white/50 hover:bg-white transition-all duration-300 shadow-sm hover:shadow-md group"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5 text-slate-600 group-hover:text-indigo-600 transition-colors" />
        
        {unreadCount > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1.5 -right-1.5 min-w-[20px] h-[20px] flex items-center justify-center bg-linear-to-tr from-indigo-600 to-violet-500 text-white text-[10px] font-bold rounded-full px-1 shadow-md shadow-indigo-500/20"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </motion.span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 z-40"
            />
            
            <motion.div
              initial={{ opacity: 0, y: 15, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 15, scale: 0.95 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="absolute right-0 top-full mt-3 w-[380px] bg-white/80 backdrop-blur-2xl rounded-2xl border border-white shadow-[0_8px_30px_rgb(0,0,0,0.12)] z-50 overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200/50 bg-white/50">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-base text-slate-900">Notifications</h3>
                  {unreadCount > 0 && (
                    <span className="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-0.5 rounded-full">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllAsRead}
                      disabled={isLoading}
                      className="text-xs font-medium text-indigo-600 hover:text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors disabled:opacity-50"
                    >
                      {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mx-auto" /> : 'Mark all read'}
                    </button>
                  )}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-slate-500" />
                  </button>
                </div>
              </div>

              {/* Notifications List */}
              <div className="max-h-[420px] overflow-y-auto p-3 space-y-2 scrollbar-thin scrollbar-thumb-slate-200">
                {notificationsList.length === 0 ? (
                  <div className="py-12 px-6 text-center flex flex-col items-center">
                    <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                      <Bell className="w-8 h-8 text-slate-300" />
                    </div>
                    <h4 className="text-slate-900 font-medium mb-1">All caught up!</h4>
                    <p className="text-sm text-slate-500">You don't have any new notifications.</p>
                  </div>
                ) : (
                  notificationsList.map((notification) => (
                    <motion.div
                      key={notification.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`relative p-4 rounded-xl border transition-all duration-300 ${getPriorityBg(notification.priority, notification.is_read)}`}
                    >
                      <div className="flex gap-3">
                        <div className={`mt-0.5 w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${notification.is_read ? 'bg-slate-100' : 'bg-white shadow-sm'}`}>
                          {getPriorityIcon(notification.priority)}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm leading-relaxed ${notification.is_read ? 'text-slate-600' : 'text-slate-900 font-medium'}`}>
                            {notification.message}
                          </p>
                          
                          <div className="flex items-center justify-between mt-3">
                            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                              {formatTime(notification.created_at)}
                            </span>
                            
                            {!notification.is_read && (
                              <button
                                onClick={(e) => handleMarkAsRead(e, notification.id)}
                                disabled={markingRead === notification.id}
                                className="flex items-center gap-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-700 px-2.5 py-1 rounded-md hover:bg-indigo-50 transition-colors disabled:opacity-50"
                              >
                                {markingRead === notification.id ? (
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                  <>
                                    <Check className="w-3 h-3" />
                                    Mark read
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                          
                          {notification.action_url && (
                            <a
                              href={notification.action_url}
                              className="inline-flex items-center mt-3 text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-white/50 px-3 py-1.5 rounded-lg hover:bg-white transition-colors border border-indigo-100"
                            >
                              View Details
                            </a>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>

              {/* Footer */}
              <div className="px-5 py-3 border-t border-slate-200/50 bg-slate-50/50 text-center">
                <a href="/notifications" className="text-xs font-medium text-slate-500 hover:text-indigo-600 transition-colors">
                  View all notifications
                </a>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
