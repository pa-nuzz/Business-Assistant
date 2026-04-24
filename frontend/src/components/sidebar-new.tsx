'use client';

import { useState, useCallback, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Menu, MessageSquare, Home, CheckSquare, FileText, Settings, 
  Plus, LogOut, User, Trash2, ChevronLeft, ChevronRight, ChevronDown, ChevronUp 
} from 'lucide-react';
import { chat, auth } from '@/lib/api';
import { toast } from 'sonner';

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
  message_count?: number;
}

const navItems = [
  { icon: Home, label: 'Dashboard', path: '/dashboard' },
  { icon: MessageSquare, label: 'Chat', path: '/chat' },
  { icon: CheckSquare, label: 'Tasks', path: '/tasks' },
  { icon: FileText, label: 'Documents', path: '/documents' },
  { icon: Settings, label: 'Settings', path: '/settings' },
];

// Animated Logo Component - works in both expanded and collapsed modes
function AnimatedLogo({ className = '', size = 32 }: { className?: string; size?: number }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <circle cx="50" cy="50" r="48" fill="white"/>
      <circle cx="50" cy="50" r="48" fill="url(#brandGradient)" fillOpacity="0.1"/>
      <rect x="20" y="45" width="8" height="35" rx="4" fill="#6366F1">
        <animate attributeName="height" values="35;25;45;35" dur="3s" repeatCount="indefinite" />
        <animate attributeName="y" values="45;55;35;45" dur="3s" repeatCount="indefinite" />
      </rect>
      <rect x="35" y="30" width="8" height="50" rx="4" fill="#8B5CF6">
        <animate attributeName="height" values="50;35;55;50" dur="2.5s" repeatCount="indefinite" />
        <animate attributeName="y" values="30;45;25;30" dur="2.5s" repeatCount="indefinite" />
      </rect>
      <rect x="50" y="20" width="8" height="60" rx="4" fill="#6366F1">
        <animate attributeName="height" values="60;40;70;60" dur="2s" repeatCount="indefinite" />
        <animate attributeName="y" values="20;40;10;20" dur="2s" repeatCount="indefinite" />
      </rect>
      <rect x="65" y="35" width="8" height="45" rx="4" fill="#8B5CF6">
        <animate attributeName="height" values="45;30;50;45" dur="2.7s" repeatCount="indefinite" />
        <animate attributeName="y" values="35;50;25;35" dur="2.7s" repeatCount="indefinite" />
      </rect>
      <rect x="80" y="50" width="8" height="30" rx="4" fill="#6366F1">
        <animate attributeName="height" values="30;20;40;30" dur="3.2s" repeatCount="indefinite" />
        <animate attributeName="y" values="50;60;40;50" dur="3.2s" repeatCount="indefinite" />
      </rect>
      <defs>
        <linearGradient id="brandGradient" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6366F1"/>
          <stop offset="1" stopColor="#8B5CF6"/>
        </linearGradient>
      </defs>
    </svg>
  );
}

// CollapsibleTooltip for collapsed sidebar
function Tooltip({ children, text }: { children: React.ReactNode; text: string }) {
  const [show, setShow] = useState(false);
  
  return (
    <div 
      className="relative"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      <AnimatePresence>
        {show && (
          <motion.div
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -5 }}
            className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded-md whitespace-nowrap z-50"
            style={{ top: '50%', transform: 'translateY(-50%)' }}
          >
            {text}
            <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 border-4 border-transparent border-r-slate-800" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Start with default values to avoid hydration mismatch
  // Actual values loaded from localStorage in useEffect after mount
  const [isCollapsed, setIsCollapsed] = useState(true); // Default: collapsed
  const [isRecentChatsExpanded, setIsRecentChatsExpanded] = useState(false); // Default: minimized
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Load persisted states AFTER mount (safe for hydration)
  useEffect(() => {
    try {
      const savedCollapsed = localStorage.getItem('sidebar-collapsed');
      if (savedCollapsed !== null) {
        setIsCollapsed(JSON.parse(savedCollapsed));
      }
      
      const savedExpanded = localStorage.getItem('recent-chats-expanded');
      if (savedExpanded !== null) {
        setIsRecentChatsExpanded(JSON.parse(savedExpanded));
      }
      
      setIsAuthenticated(auth.isAuthenticated());
    } catch {
      // Ignore localStorage errors
    }
  }, []);
  
  // Persist states to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('sidebar-collapsed', JSON.stringify(isCollapsed));
    } catch {
      // Ignore localStorage errors
    }
  }, [isCollapsed]);
  
  useEffect(() => {
    try {
      localStorage.setItem('recent-chats-expanded', JSON.stringify(isRecentChatsExpanded));
    } catch {
      // Ignore localStorage errors
    }
  }, [isRecentChatsExpanded]);

  // Fetch conversations once on mount
  useEffect(() => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }

    const fetchConversations = async () => {
      try {
        const data = await chat.getConversations();
        const filtered = (data?.results || []).filter(
          (conv: any) => conv.message_count > 0 && conv.title !== 'Untitled conversation'
        );
        setConversations(filtered.slice(0, 15));
      } catch {
        // Silent fail
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
    
    // Refresh every 30 seconds only when visible
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchConversations();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileOpen(false);
  }, [pathname]);

  const handleNewChat = useCallback(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    router.push('/chat');
    setIsMobileOpen(false);
  }, [isAuthenticated, router]);

  const handleLogout = useCallback(() => {
    auth.logout();
    router.push('/login');
    toast.success('Logged out successfully');
  }, [router]);

  const handleDeleteConversation = useCallback(async (e: React.MouseEvent, id: string, title: string) => {
    e.stopPropagation();
    
    if (!confirm(`Delete "${title || 'Untitled'}"?`)) return;
    
    setDeletingId(id);
    try {
      await chat.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      toast.success('Conversation deleted');
    } catch {
      toast.error('Failed to delete');
    } finally {
      setDeletingId(null);
    }
  }, []);

  // SidebarContent handles both expanded and collapsed states
  const SidebarContent = () => {
    if (isCollapsed) {
      // COLLAPSED STATE: Icon-only sidebar
      return (
        <div className="flex flex-col h-full bg-white border-r border-slate-200 w-[72px]">
          {/* Logo - Centered */}
          <div className="h-16 flex items-center justify-center border-b border-slate-100 flex-shrink-0">
            <Tooltip text="AEIOU AI">
              <AnimatedLogo size={28} />
            </Tooltip>
          </div>

          {/* New Chat Button - Icon only */}
          <div className="p-3 flex-shrink-0">
            <Tooltip text="New Chat">
              <button
                onClick={handleNewChat}
                className="w-12 h-12 flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
              >
                <Plus className="w-5 h-5" />
              </button>
            </Tooltip>
          </div>

          {/* Navigation - Icons only */}
          <nav className="px-3 py-2 flex-shrink-0 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path || pathname?.startsWith(`${item.path}/`);
              
              return (
                <Tooltip key={item.path} text={item.label}>
                  <button
                    onClick={() => router.push(item.path)}
                    className={`w-12 h-12 flex items-center justify-center rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer ${
                      isActive 
                        ? 'bg-indigo-50 text-indigo-700' 
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? 'text-indigo-600' : 'text-slate-500'}`} />
                  </button>
                </Tooltip>
              );
            })}
          </nav>

          {/* Expand Button at bottom of nav area */}
          <div className="flex-1" />
          
          {/* Footer */}
          <div className="p-3 border-t border-slate-100 flex-shrink-0">
            <Tooltip text={isAuthenticated ? "Logout" : "Login"}>
              <button
                onClick={isAuthenticated ? handleLogout : () => router.push('/login')}
                className={`w-12 h-12 flex items-center justify-center rounded-xl transition-all duration-200 ${
                  isAuthenticated 
                    ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-50' 
                    : 'text-white bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                {isAuthenticated ? <LogOut className="w-5 h-5" /> : <User className="w-5 h-5" />}
              </button>
            </Tooltip>
          </div>
        </div>
      );
    }

    // EXPANDED STATE: Full sidebar
    return (
      <div className="flex flex-col h-full bg-white border-r border-slate-200">
        {/* Logo / Brand with collapse toggle */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100 flex-shrink-0">
          <div className="flex items-center gap-3">
            <AnimatedLogo className="w-8 h-8 flex-shrink-0" />
            <span className="font-semibold text-slate-900 text-base">AEIOU AI</span>
          </div>
          <button
            onClick={() => setIsCollapsed(true)}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all"
            title="Collapse sidebar"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4 flex-shrink-0">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium text-sm transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Navigation */}
        <nav className="px-3 pb-2 flex-shrink-0">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path || pathname?.startsWith(`${item.path}/`);
            
            return (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer mb-0.5 ${
                  isActive 
                    ? 'bg-indigo-50 text-indigo-700' 
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-indigo-600' : 'text-slate-500'}`} />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Recent Chats Section - Minimizable */}
        {isAuthenticated && (
          <div className="flex-1 overflow-hidden flex flex-col min-h-0 mt-2">
            {/* Section Header with Toggle */}
            <button
              onClick={() => setIsRecentChatsExpanded(!isRecentChatsExpanded)}
              className="px-4 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Recent Chats
                </span>
                {conversations.length > 0 && (
                  <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                    {conversations.length}
                  </span>
                )}
              </div>
              {isRecentChatsExpanded ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>
            
            {/* Expandable Content */}
            <AnimatePresence initial={false}>
              {isRecentChatsExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2, ease: 'easeInOut' }}
                  className="overflow-hidden"
                >
                  <div className="flex-1 overflow-y-auto px-2 space-y-1 pb-2">
                    {isLoading ? (
                      <div className="space-y-2 px-2 py-1">
                        {[...Array(3)].map((_, i) => (
                          <div key={i} className="h-10 bg-slate-100 rounded-lg animate-pulse" />
                        ))}
                      </div>
                    ) : conversations.length === 0 ? (
                      <div className="px-4 py-6 text-sm text-slate-400 text-center">
                        No conversations yet
                      </div>
                    ) : (
                      conversations.map((conv) => {
                        const isActive = pathname === '/chat' && new URLSearchParams(window.location.search).get('id') === conv.id;
                        
                        return (
                          <div
                            key={conv.id}
                            className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 cursor-pointer ${
                              isActive 
                                ? 'bg-indigo-50 text-slate-900' 
                                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                            }`}
                            onClick={() => router.push(`/chat?id=${conv.id}`)}
                          >
                            <MessageSquare className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                            <span className="flex-1 truncate min-w-0">{conv.title || 'Untitled'}</span>
                            <button
                              onClick={(e) => handleDeleteConversation(e, conv.id, conv.title)}
                              disabled={deletingId === conv.id}
                              className="flex-shrink-0 p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-all opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                              title="Delete conversation"
                            >
                              {deletingId === conv.id ? (
                                <span className="w-3.5 h-3.5 border-2 border-slate-300 border-t-red-500 rounded-full animate-spin block" />
                              ) : (
                                <Trash2 className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        );
                      })
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Footer */}
        <div className="p-3 border-t border-slate-100 flex-shrink-0 mt-auto">
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-all duration-200"
            >
              <LogOut className="w-4 h-4 flex-shrink-0" />
              <span className="truncate">Logout</span>
            </button>
          ) : (
            <button
              onClick={() => router.push('/login')}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-all duration-200"
            >
              <User className="w-4 h-4 flex-shrink-0" />
              <span className="truncate">Login</span>
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Mobile Menu Button - Positioned properly to not overlap content */}
      <motion.button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        whileTap={{ scale: 0.95 }}
        className="lg:hidden fixed top-4 left-4 z-50 w-10 h-10 bg-white rounded-xl shadow-lg border border-slate-200 flex items-center justify-center"
      >
        {isMobileOpen ? <X className="w-5 h-5 text-slate-700" /> : <Menu className="w-5 h-5 text-slate-700" />}
      </motion.button>

      {/* Desktop Sidebar - Dynamic width based on collapsed state */}
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 72 : 280 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="hidden lg:flex flex-shrink-0 h-screen flex-col sticky top-0 overflow-hidden"
      >
        <SidebarContent />
      </motion.aside>

      {/* Floating expand button when collapsed (desktop only) */}
      {!isMobileOpen && isCollapsed && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.05 }}
          onClick={() => setIsCollapsed(false)}
          className="hidden lg:flex fixed bottom-6 left-[84px] z-40 w-8 h-8 bg-white border border-slate-200 shadow-md rounded-full items-center justify-center text-slate-500 hover:text-indigo-600 hover:border-indigo-300 transition-all"
          title="Expand sidebar"
        >
          <ChevronRight className="w-4 h-4" />
        </motion.button>
      )}

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileOpen(false)}
              className="lg:hidden fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="lg:hidden fixed top-0 left-0 w-[280px] h-screen flex flex-col bg-white border-r border-slate-200 z-50"
            >
              {/* Mobile close button header */}
              <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100 flex-shrink-0">
                <div className="flex items-center gap-3">
                  <AnimatedLogo className="w-8 h-8 flex-shrink-0" />
                  <span className="font-semibold text-slate-900 text-base">AEIOU AI</span>
                </div>
                <button
                  onClick={() => setIsMobileOpen(false)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                <SidebarContent />
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
