'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, MessageSquare, FileText, BarChart2, Settings, 
  LogOut, User, Plus, X, Command, Keyboard,
  History, Clock
} from 'lucide-react';
import { auth } from '@/lib/api';
import { toast } from 'sonner';
import Fuse from 'fuse.js';

interface CommandItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  keywords?: string[];
  action: () => void;
}

function KeyboardShortcutsHelp({ onClose }: { onClose: () => void }) {
  const shortcuts = [
    { key: '⌘ K', description: 'Open command palette' },
    { key: 'C', description: 'Go to Chat' },
    { key: 'D', description: 'Go to Documents' },
    { key: 'B', description: 'Go to Dashboard' },
    { key: 'S', description: 'Go to Settings' },
    { key: 'N', description: 'New Chat' },
    { key: 'Esc', description: 'Close/Cancel' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: -20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -20 }}
      transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
      className="fixed top-1/4 left-1/2 -translate-x-1/2 w-full max-w-md z-50 overflow-hidden"
    >
      <div className="relative bg-white/80 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/40 overflow-hidden">
        <div className="px-6 py-4 bg-linear-to-r from-indigo-500/10 to-violet-400/10 border-b border-white/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-linear-to-br from-indigo-500 to-violet-400 flex items-center justify-center shadow-lg">
              <Keyboard className="w-5 h-5 text-slate-900" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">Keyboard Shortcuts</h2>
              <p className="text-xs text-slate-500">Press any key to navigate</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/50 rounded-xl transition-colors">
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 gap-3">
            {shortcuts.map((shortcut, index) => (
              <motion.div
                key={shortcut.key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center justify-between p-3 rounded-xl bg-white/60 hover:bg-white/80 transition-colors border border-white/40"
              >
                <span className="text-sm text-slate-600">{shortcut.description}</span>
                <kbd className="px-2.5 py-1 bg-linear-to-b from-slate-100 to-slate-200 border border-slate-300 rounded-lg text-xs font-mono font-semibold text-slate-700 shadow-sm">
                  {shortcut.key}
                </kbd>
              </motion.div>
            ))}
          </div>
        </div>
        <div className="px-6 py-3 bg-slate-50/50 border-t border-white/30 text-center">
          <p className="text-xs text-slate-400">Pro tip: Use Cmd/Ctrl + letter for quick navigation</p>
        </div>
      </div>
    </motion.div>
  );
}

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [search, setSearch] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleOpenHelp = () => setShowHelp(true);
    window.addEventListener('open-help', handleOpenHelp);
    return () => window.removeEventListener('open-help', handleOpenHelp);
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem('recent-commands');
    if (saved) setRecentCommands(JSON.parse(saved));
  }, []);

  const saveRecentCommand = (commandId: string) => {
    const updated = [commandId, ...recentCommands.filter(id => id !== commandId)].slice(0, 5);
    setRecentCommands(updated);
    localStorage.setItem('recent-commands', JSON.stringify(updated));
  };

  const commands: CommandItem[] = [
    {
      id: 'search',
      label: 'Global Semantic Search',
      icon: <Search size={16} />,
      shortcut: '/',
      keywords: ['search', 'find', 'rag', 'ask'],
      action: () => router.push('/chat?action=search'),
    },
    {
      id: 'chat',
      label: 'Go to Chat',
      icon: <MessageSquare size={16} />,
      shortcut: 'C',
      keywords: ['chat', 'message', 'conversation', 'talk'],
      action: () => router.push('/chat'),
    },
    {
      id: 'documents',
      label: 'Go to Documents',
      icon: <FileText size={16} />,
      shortcut: 'D',
      keywords: ['document', 'file', 'upload', 'pdf'],
      action: () => router.push('/documents'),
    },
    {
      id: 'dashboard',
      label: 'Go to Dashboard',
      icon: <BarChart2 size={16} />,
      shortcut: 'B',
      keywords: ['dashboard', 'analytics', 'metrics', 'stats'],
      action: () => router.push('/dashboard'),
    },
    {
      id: 'settings',
      label: 'Go to Settings',
      icon: <Settings size={16} />,
      shortcut: 'S',
      keywords: ['settings', 'preferences', 'profile', 'account'],
      action: () => router.push('/settings'),
    },
    {
      id: 'new-chat',
      label: 'New Chat',
      icon: <Plus size={16} />,
      shortcut: 'N',
      keywords: ['new', 'create', 'start'],
      action: () => router.push('/chat'),
    },
    {
      id: 'logout',
      label: 'Logout',
      icon: <LogOut size={16} />,
      keywords: ['logout', 'sign out', 'exit', 'quit'],
      action: () => {
        auth.logout();
        router.push('/login');
      },
    },
  ];

  const fuse = new Fuse(commands, {
    keys: ['label', 'keywords'],
    threshold: 0.4,
  });

  const filteredCommands = search 
    ? fuse.search(search).map(result => result.item)
    : recentCommands.length > 0
      ? [
          ...recentCommands.map(id => commands.find(c => c.id === id)).filter(Boolean) as CommandItem[],
          ...commands.filter(c => !recentCommands.includes(c.id)),
        ]
      : commands;

  const handleCommand = (cmd: CommandItem) => {
    saveRecentCommand(cmd.id);
    setIsOpen(false);
    cmd.action();
    setSearch('');
  };

  const handleSmartAction = async (query: string) => {
    if (!query.trim() || isProcessing) return;
    setIsProcessing(true);
    try {
      const response = await fetch('/api/v1/actions/smart/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.getToken()}`,
        },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      if (data.action === 'NAVIGATE') {
        router.push(`/${data.params.to}`);
      } else if (data.action === 'CREATE_TASK') {
        toast.success(`Task Created: ${data.params.title}`);
      } else if (data.action === 'SEARCH') {
        router.push(`/chat?query=${encodeURIComponent(data.params.query)}&type=${data.params.type}`);
      } else if (data.action === 'ANALYZE') {
        toast.info(`Analyzing ${data.params.target}...`);
        router.push('/dashboard');
      } else {
        router.push(`/chat?query=${encodeURIComponent(query)}`);
      }
      setIsOpen(false);
    } catch (err) {
      toast.error('Failed to execute smart command');
    } finally {
      setIsProcessing(false);
      setSearch('');
    }
  };

  const handleKeyDownInInput = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (filteredCommands.length > 0 && search.length > 0) {
        const topMatch = filteredCommands[0];
        if (topMatch.label.toLowerCase() === search.toLowerCase()) {
          handleCommand(topMatch);
          return;
        }
      }
      if (search.trim()) handleSmartAction(search);
    }
  };

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (!auth.isAuthenticated()) {
        router.push('/login');
        return;
      }
      setIsOpen(true);
      setShowHelp(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
    if (e.key === 'Escape') {
      if (showHelp) setShowHelp(false);
      else setIsOpen(false);
    }
  }, [showHelp, router]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <>
      {auth.isAuthenticated() && (
        <motion.button
          onClick={() => setIsOpen(true)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="fixed bottom-4 right-4 z-40 flex items-center gap-2 px-3 py-2 bg-white/80 backdrop-blur-md border border-slate-200/80 rounded-xl shadow-lg text-sm text-slate-600 hover:text-slate-900 transition-all"
        >
          <Command size={14} className="text-indigo-500" />
          <span className="font-medium">Cmd K</span>
        </motion.button>
      )}

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
              className="fixed top-1/4 left-1/2 -translate-x-1/2 w-full max-w-lg bg-white/85 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/40 z-50 overflow-hidden"
            >
              <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200/50 bg-linear-to-r from-indigo-50/50 to-violet-50/50">
                {isProcessing ? (
                  <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Search size={20} className="text-indigo-500" />
                )}
                <input
                  ref={inputRef}
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={handleKeyDownInInput}
                  placeholder={isProcessing ? "Processing command..." : "Search or type a command (e.g. 'Go to tasks')..."}
                  className="flex-1 bg-transparent border-none outline-none text-sm text-slate-800 placeholder:text-slate-400"
                  disabled={isProcessing}
                  autoFocus
                />
                <button onClick={() => setIsOpen(false)} className="p-1.5 hover:bg-white/80 rounded-lg transition-colors">
                  <X size={16} className="text-slate-400" />
                </button>
              </div>

              {!search && recentCommands.length > 0 && (
                <div className="px-4 py-2 bg-slate-50/50 border-b border-slate-200/30 flex items-center gap-2">
                  <History size={12} className="text-slate-400" />
                  <span className="text-xs text-slate-400">Recent commands</span>
                </div>
              )}

              <div className="max-h-[300px] overflow-y-auto py-2">
                {filteredCommands.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-slate-500">
                    {search ? `Press Enter to run "${search}" as a smart command` : "No commands found"}
                  </div>
                ) : (
                  filteredCommands.map((cmd, index) => {
                    const isRecent = recentCommands.includes(cmd.id) && !search;
                    return (
                      <motion.button
                        key={cmd.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.03 }}
                        onClick={() => handleCommand(cmd)}
                        className={`w-full flex items-center justify-between px-4 py-2.5 hover:bg-indigo-50/60 transition-colors text-left group ${isRecent ? 'bg-indigo-50/30' : ''}`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-indigo-500/70 group-hover:text-indigo-600 transition-colors">{cmd.icon}</span>
                          <span className="text-sm text-slate-700 group-hover:text-slate-900">{cmd.label}</span>
                          {isRecent && <Clock size={12} className="text-indigo-400" />}
                        </div>
                        {cmd.shortcut && (
                          <kbd className="px-2 py-0.5 bg-slate-100 group-hover:bg-white border border-slate-200 rounded text-xs text-slate-500 font-medium">
                            {cmd.shortcut}
                          </kbd>
                        )}
                      </motion.button>
                    );
                  })
                )}
              </div>

              <div className="px-4 py-2.5 bg-slate-50/70 border-t border-slate-200/50 flex items-center justify-between text-xs text-slate-500">
                <span>{search ? "AI-Powered Command Active" : "Press Enter to select"}</span>
                <div className="flex items-center gap-1">
                  <Command size={10} />
                  <span>K to close</span>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showHelp && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowHelp(false)}
              className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-50"
            />
            <KeyboardShortcutsHelp onClose={() => setShowHelp(false)} />
          </>
        )}
      </AnimatePresence>
    </>
  );
}
