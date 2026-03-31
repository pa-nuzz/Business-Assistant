'use client';

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { MessageSquare, FileText, BarChart2, Plus, LogOut, X } from 'lucide-react';
import { chat, auth } from '@/lib/api';

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
  const [isLoading, setIsLoading] = useState(true);
  const [isShaking, setIsShaking] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  // Check auth synchronously for initial render
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const isAuthenticated = !!token;

  useEffect(() => {
    if (token) {
      chat.getConversations().then((data) => {
        setConversations(data.slice(0, 20));
      }).catch(() => {});

      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUsername(payload.username || 'User');
      } catch {
        setUsername('User');
      }
    }
    setIsLoading(false);
  }, []);

  const handleLogout = () => {
    auth.logout();
    router.push('/login');
  };

  const handleNewChat = () => {
    if (!isAuthenticated) {
      triggerShakeAndRedirect();
      return;
    }
    router.push('/chat');
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
    { path: '/dashboard', icon: BarChart2, label: 'Dashboard' },
  ];

  const isActive = (path: string) => pathname === path || pathname.startsWith(`${path}/`);
  const initials = username.slice(0, 2).toUpperCase();

  const shakeStyles = isShaking ? { animation: 'shake 0.3s ease-in-out' } : {};

  if (isLoading) {
    return (
      <aside className="w-[260px] flex-shrink-0 h-screen bg-white border-r border-gray-200" />
    );
  }

  return (
    <aside
      className={`w-[260px] flex-shrink-0 h-screen flex flex-col bg-white border-r border-gray-200 px-3 ${shakeStyles}`}
    >
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
      <div
        style={{
          height: '48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 4px',
        }}
      >
        <span
          style={{
            fontSize: '14px',
            fontWeight: 500,
            color: 'var(--ink-0)',
          }}
        >
          Business Assistant
        </span>
        <button
          onClick={handleNewChat}
          className="flex items-center gap-1 text-[13px] text-gray-600 hover:text-black bg-transparent border-none cursor-pointer px-2 py-1 rounded-md transition-colors hover:bg-gray-100"
        >
          <Plus size={14} />
          New chat
        </button>
      </div>

      {/* Nav Links */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '8px' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <a
              key={item.path}
              href={item.path}
              onClick={(e) => handleNavClick(e, item.path)}
              className={`flex items-center gap-2.5 px-3 py-2 text-[14px] font-normal rounded-r-lg transition-all cursor-pointer no-underline ${
                active 
                  ? 'text-black bg-gray-100 border-l-2 border-black font-medium' 
                  : 'text-gray-600 hover:text-black hover:bg-gray-50 border-l-2 border-transparent'
              }`}
            >
              <Icon size={16} className={active ? 'text-black' : ''} />
              {item.label}
            </a>
          );
        })}
      </nav>

      {/* Recent Conversations - Only show when authenticated */}
      {isAuthenticated && (
        <div style={{ marginTop: '24px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 12px', marginBottom: '8px' }}>
            <span
              style={{
                fontSize: '11px',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--ink-3)',
              }}
            >
              Recent
            </span>
          </div>
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {conversations.map((conv) => {
              const active = pathname === `/chat` && conv.id === (typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('id') : '');
              return (
                <div
                  key={conv.id}
                  className="conversation-item"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '2px 4px',
                    borderRadius: '6px',
                    backgroundColor: active ? 'var(--surface-2)' : 'transparent',
                    marginBottom: '2px',
                  }}
                >
                  <a
                    href={`/chat?id=${conv.id}`}
                    onClick={(e) => handleNavClick(e, `/chat?id=${conv.id}`)}
                    style={{
                      display: 'block',
                      flex: 1,
                      padding: '6px 8px',
                      fontSize: '13px',
                      color: 'var(--ink-1)',
                      textDecoration: 'none',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      cursor: 'pointer',
                    }}
                    title={conv.title}
                  >
                    {conv.title || 'Untitled conversation'}
                  </a>
                  <button
                    onClick={(e) => handleDeleteConversation(e, conv.id)}
                    disabled={deletingId === conv.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '22px',
                      height: '22px',
                      borderRadius: '4px',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: 'var(--ink-3)',
                      opacity: 0,
                      transition: 'opacity 120ms ease',
                    }}
                    title="Delete"
                  >
                    {deletingId === conv.id ? <span style={{ fontSize: '10px' }}>...</span> : <X size={12} />}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Bottom: User Info + Logout */}
      <div
        style={{
          padding: '12px',
          borderTop: '1px solid var(--surface-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium ${
              isAuthenticated 
                ? 'bg-gray-200 text-black' 
                : 'bg-gray-100 text-gray-500'
            }`}
          >
            {isAuthenticated ? initials : '?'}
          </div>
          <span style={{ fontSize: '13px', color: isAuthenticated ? 'var(--ink-1)' : 'var(--ink-2)' }}>
            {isAuthenticated ? username : 'Guest'}
          </span>
        </div>
        {isAuthenticated ? (
          <button
            onClick={handleLogout}
            className="flex items-center justify-center w-7 h-7 rounded-md bg-transparent border-none cursor-pointer text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            title="Logout"
          >
            <LogOut size={14} />
          </button>
        ) : (
          <button
            onClick={() => router.push('/login')}
            className="flex items-center justify-center w-7 h-7 rounded-md bg-transparent border-none cursor-pointer text-gray-600 hover:text-black hover:bg-gray-100 transition-colors"
            title="Login"
          >
            <LogOut size={14} />
          </button>
        )}
      </div>
    </aside>
  );
}
