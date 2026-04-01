'use client';

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, FileText, BarChart2, Plus, LogOut, X, User, Menu,
  CheckSquare
} from 'lucide-react';
import { chat, auth, user } from '@/lib/api';

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

export default function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [username, setUsername] = useState('');
  const [avatar, setAvatar] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isShaking, setIsShaking] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const isAuthenticated = !!token;

  useEffect(() => {
    if (token) {
      chat.getConversations().then((data) => {
        setConversations(data.slice(0, 20));
      }).catch(() => {});

      user.getInfo().then((data) => {
        setUsername(data.username || 'User');
        setAvatar(data.avatar || null);
      }).catch(() => {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          setUsername(payload.username || 'User');
        } catch {
          setUsername('User');
        }
      });
    }
    setIsLoading(false);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  // Refresh conversations when pathname changes
  useEffect(() => {
    if (token && pathname === '/chat') {
      chat.getConversations().then((data) => {
        setConversations(data.slice(0, 20));
      }).catch(() => {});
    }
  }, [pathname, token]);

  const handleLogout = () => {
    auth.logout();
    router.push('/login');
    setIsMobileMenuOpen(false);
  };

  const handleNewChat = () => {
    if (!isAuthenticated) {
      triggerShakeAndRedirect();
      return;
    }
    router.push('/chat');
    setIsMobileMenuOpen(false);
  };

  const triggerShakeAndRedirect = () => {
    setIsShaking(true);
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate([50, 100, 50]);
    }
    setTimeout(() => {
      setIsShaking(false);
      router.push('/login');
    }, 300);
  };

  const handleNavClick = (e: React.MouseEvent, path: string) => {
    if (!isAuthenticated) {
      e.preventDefault();
      triggerShakeAndRedirect();
    }
    setIsMobileMenuOpen(false);
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;
    setDeletingId(id);
    try {
      await chat.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
    } catch (err) {
      alert('Failed to delete conversation');
    } finally {
      setDeletingId(null);
    }
  };

  const navItems = [
    { path: '/chat', icon: MessageSquare, label: 'Chat' },
    { path: '/documents', icon: FileText, label: 'Documents' },
    { path: '/tasks', icon: CheckSquare, label: 'Tasks' },
    { path: '/dashboard', icon: BarChart2, label: 'Dashboard' },
  ];

  const isActive = (path: string) => pathname === path || pathname.startsWith(`${path}/`);

  const SidebarContent = () => (
    <>
      <style jsx>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          50% { transform: translateX(5px); }
          75% { transform: translateX(-5px); }
        }
        .conversation-item:hover button { opacity: 1 !important; }
      `}</style>
      
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-3 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-400 flex items-center justify-center">
            <MessageSquare size={16} className="text-white" />
          </div>
          <span className="text-sm font-semibold text-foreground">
            AEIOU AI
          </span>
        </div>
        <button
          onClick={handleNewChat}
          className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground bg-muted hover:bg-muted/80 rounded-full px-3 py-1.5 transition-all"
        >
          <Plus size={14} />
          New
        </button>
      </div>

      {/* Nav Links */}
      <nav className="flex flex-col gap-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <motion.a
              key={item.path}
              href={item.path}
              onClick={(e) => handleNavClick(e, item.path)}
              whileHover={{ x: 2 }}
              whileTap={{ scale: 0.98 }}
              className={`flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-lg transition-all cursor-pointer no-underline ${
                active 
                  ? 'text-foreground bg-blue-50 border border-blue-100' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted border border-transparent'
              }`}
            >
              <Icon size={18} className={active ? 'text-blue-600' : ''} />
              {item.label}
            </motion.a>
          );
        })}
      </nav>

      {/* Recent Conversations - Only show when authenticated */}
      {isAuthenticated && (
        <div className="mt-2 flex-1 overflow-hidden flex flex-col px-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Recent
            </span>
          </div>
          <div className="overflow-y-auto flex-1 space-y-1">
            {conversations.map((conv) => {
              const active = pathname === `/chat` && conv.id === (typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('id') : '');
              return (
                <motion.div
                  key={conv.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="conversation-item flex items-center group"
                >
                  <a
                    href={`/chat?id=${conv.id}`}
                    onClick={(e) => handleNavClick(e, `/chat?id=${conv.id}`)}
                    className={`block flex-1 px-3 py-2 text-sm rounded-lg no-underline truncate cursor-pointer transition-all ${
                      active 
                        ? 'text-foreground bg-blue-50 font-medium' 
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                    }`}
                    title={conv.title}
                  >
                    {conv.title || 'Untitled conversation'}
                  </a>
                  <button
                    onClick={(e) => handleDeleteConversation(e, conv.id)}
                    disabled={deletingId === conv.id}
                    className="flex items-center justify-center w-7 h-7 rounded-md bg-transparent border-none cursor-pointer text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
                    title="Delete"
                  >
                    {deletingId === conv.id ? <span className="text-[10px]">...</span> : <X size={14} />}
                  </button>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Bottom: User Info + Logout */}
      <div className="p-3 border-t border-border mt-auto">
        <div className="flex items-center gap-3 bg-muted rounded-lg p-2">
          <a
            href="/settings"
            className="flex items-center gap-3 flex-1 cursor-pointer hover:opacity-80 transition-opacity"
          >
            <div 
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium overflow-hidden ${
                isAuthenticated 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {avatar ? (
                <img src={avatar} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <User size={14} />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-sm font-medium text-foreground truncate block">
                {isAuthenticated ? username : 'Guest'}
              </span>
            </div>
          </a>
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="flex items-center justify-center w-8 h-8 rounded-md bg-transparent border-none cursor-pointer text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all"
              title="Logout"
            >
              <LogOut size={14} />
            </button>
          ) : (
            <button
              onClick={() => router.push('/login')}
              className="flex items-center justify-center w-8 h-8 rounded-md bg-transparent border-none cursor-pointer text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
              title="Login"
            >
              <LogOut size={14} />
            </button>
          )}
        </div>
      </div>
    </>
  );

  const shakeStyles = isShaking ? { animation: 'shake 0.3s ease-in-out' } : {};

  if (isLoading) {
    return (
      <aside className="hidden lg:block w-[280px] flex-shrink-0 h-screen bg-background border-r border-border" />
    );
  }

  return (
    <>
      {/* Mobile Menu Button */}
      <motion.button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        whileTap={{ scale: 0.95 }}
        className="lg:hidden fixed top-4 left-4 z-50 w-10 h-10 bg-card rounded-xl shadow-lg border border-border flex items-center justify-center"
      >
        <Menu size={20} className="text-foreground" />
      </motion.button>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-[280px] flex-shrink-0 h-screen flex-col bg-background border-r border-border" style={shakeStyles}>
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileMenuOpen(false)}
              className="lg:hidden fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="lg:hidden fixed top-0 left-0 w-[280px] h-screen flex flex-col bg-background border-r border-border z-50"
              style={shakeStyles}
            >
              <div className="flex items-center justify-end h-14 px-3 border-b border-border">
                <button
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-muted transition-colors"
                >
                  <X size={20} className="text-foreground" />
                </button>
              </div>
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
