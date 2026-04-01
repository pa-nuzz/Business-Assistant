'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, MessageSquare, FileText, BarChart2, Settings, 
  LogOut, User, Plus, X, Command
} from 'lucide-react';
import { auth } from '@/lib/api';

interface CommandItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
}

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const router = useRouter();

  const commands: CommandItem[] = [
    {
      id: 'chat',
      label: 'Go to Chat',
      icon: <MessageSquare size={16} />,
      shortcut: 'C',
      action: () => router.push('/chat'),
    },
    {
      id: 'documents',
      label: 'Go to Documents',
      icon: <FileText size={16} />,
      shortcut: 'D',
      action: () => router.push('/documents'),
    },
    {
      id: 'dashboard',
      label: 'Go to Dashboard',
      icon: <BarChart2 size={16} />,
      shortcut: 'B',
      action: () => router.push('/dashboard'),
    },
    {
      id: 'settings',
      label: 'Go to Settings',
      icon: <Settings size={16} />,
      shortcut: 'S',
      action: () => router.push('/settings'),
    },
    {
      id: 'new-chat',
      label: 'New Chat',
      icon: <Plus size={16} />,
      shortcut: 'N',
      action: () => router.push('/chat'),
    },
    {
      id: 'logout',
      label: 'Logout',
      icon: <LogOut size={16} />,
      action: () => {
        auth.logout();
        router.push('/login');
      },
    },
  ];

  const filteredCommands = commands.filter(cmd => 
    cmd.label.toLowerCase().includes(search.toLowerCase())
  );

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Cmd+K or Ctrl+K to open
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      setIsOpen(true);
    }
    // Escape to close
    if (e.key === 'Escape') {
      setIsOpen(false);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const handleCommand = (cmd: CommandItem) => {
    cmd.action();
    setIsOpen(false);
    setSearch('');
  };

  return (
    <>
      {/* Keyboard shortcut hint */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-40 flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg shadow-sm text-sm text-gray-500 hover:text-gray-700 hover:border-gray-300 transition-all hover:scale-105"
      >
        <Command size={14} />
        <span>Cmd K</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/50 z-50"
            />

            {/* Command Palette */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ duration: 0.15 }}
              className="fixed top-1/4 left-1/2 -translate-x-1/2 w-full max-w-lg bg-white rounded-xl shadow-2xl border border-gray-200 z-50 overflow-hidden"
            >
              {/* Search Input */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200">
                <Search size={20} className="text-gray-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search commands..."
                  className="flex-1 bg-transparent border-none outline-none text-sm text-gray-900 placeholder:text-gray-400"
                  autoFocus
                />
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-100 rounded-md transition-colors"
                >
                  <X size={16} className="text-gray-400" />
                </button>
              </div>

              {/* Commands List */}
              <div className="max-h-[300px] overflow-y-auto py-2">
                {filteredCommands.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-gray-500">
                    No commands found
                  </div>
                ) : (
                  filteredCommands.map((cmd) => (
                    <button
                      key={cmd.id}
                      onClick={() => handleCommand(cmd)}
                      className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 transition-colors text-left"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-gray-500">{cmd.icon}</span>
                        <span className="text-sm text-gray-700">{cmd.label}</span>
                      </div>
                      {cmd.shortcut && (
                        <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-200 rounded text-xs text-gray-500">
                          {cmd.shortcut}
                        </kbd>
                      )}
                    </button>
                  ))
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
                <span>Press Enter to select</span>
                <span>ESC to close</span>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
