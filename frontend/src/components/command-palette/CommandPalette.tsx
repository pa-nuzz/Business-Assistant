'use client';

import { useEffect, useState, useCallback } from 'react';
import { Command } from 'cmdk';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { 
  MessageSquare, 
  FileText, 
  CheckSquare, 
  Settings, 
  Search,
  Upload,
  Plus,
  LayoutDashboard,
  LogOut
} from 'lucide-react';

interface CommandItem {
  id: string;
  title: string;
  shortcut?: string;
  icon: React.ReactNode;
  action: () => void;
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const commands: CommandItem[] = [
    {
      id: 'chat',
      title: 'Ask Aiden',
      shortcut: 'G C',
      icon: <MessageSquare className="w-4 h-4" />,
      action: () => router.push('/chat'),
    },
    {
      id: 'upload',
      title: 'Upload Document',
      shortcut: 'G D',
      icon: <Upload className="w-4 h-4" />,
      action: () => router.push('/documents'),
    },
    {
      id: 'task',
      title: 'New Task',
      shortcut: 'G T',
      icon: <Plus className="w-4 h-4" />,
      action: () => router.push('/tasks'),
    },
    {
      id: 'documents',
      title: 'Go to Documents',
      icon: <FileText className="w-4 h-4" />,
      action: () => router.push('/documents'),
    },
    {
      id: 'tasks',
      title: 'Go to Tasks',
      icon: <CheckSquare className="w-4 h-4" />,
      action: () => router.push('/tasks'),
    },
    {
      id: 'dashboard',
      title: 'Go to Dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
      action: () => router.push('/dashboard'),
    },
    {
      id: 'settings',
      title: 'Settings',
      icon: <Settings className="w-4 h-4" />,
      action: () => router.push('/settings'),
    },
    {
      id: 'search',
      title: 'Search Documents...',
      icon: <Search className="w-4 h-4" />,
      action: () => {
        // TODO: Implement document search
        setOpen(false);
      },
    },
  ];

  // Toggle with ⌘K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const handleSelect = useCallback((item: CommandItem) => {
    item.action();
    setOpen(false);
  }, []);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="fixed inset-0 bg-black/60 z-[var(--z-command)]"
          />
          
          {/* Command Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 flex items-start justify-center pt-[20vh] z-[var(--z-command)]"
          >
            <Command
              className="w-full max-w-[640px] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-overlay)] shadow-[var(--shadow-lg)] overflow-hidden"
              label="Command Palette"
            >
              {/* Search Input */}
              <div className="flex items-center border-b border-[var(--border-default)] px-4">
                <Search className="w-5 h-5 text-[var(--text-muted)]" />
                <Command.Input
                  placeholder="What do you need?"
                  className="w-full bg-transparent px-3 py-4 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none"
                  autoFocus
                />
                <kbd className="px-2 py-1 text-xs text-[var(--text-muted)] bg-[var(--bg-subtle)] rounded">
                  ⌘K
                </kbd>
              </div>

              {/* Command List */}
              <Command.List className="max-h-[400px] overflow-y-auto p-2">
                <Command.Empty className="py-8 text-center text-[var(--text-secondary)]">
                  No results found
                </Command.Empty>

                <Command.Group heading="Quick Actions">
                  {commands.slice(0, 3).map((item) => (
                    <CommandItem key={item.id} item={item} onSelect={handleSelect} />
                  ))}
                </Command.Group>

                <Command.Group heading="Navigation">
                  {commands.slice(3, 7).map((item) => (
                    <CommandItem key={item.id} item={item} onSelect={handleSelect} />
                  ))}
                </Command.Group>

                <Command.Group heading="Other">
                  {commands.slice(7).map((item) => (
                    <CommandItem key={item.id} item={item} onSelect={handleSelect} />
                  ))}
                </Command.Group>
              </Command.List>

              {/* Footer */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--border-default)] text-xs text-[var(--text-muted)]">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-[var(--bg-subtle)] rounded">↑↓</kbd>
                    to navigate
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-[var(--bg-subtle)] rounded">↵</kbd>
                    to select
                  </span>
                </div>
                <span>AEIOU Command Palette</span>
              </div>
            </Command>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function CommandItem({ item, onSelect }: { item: CommandItem; onSelect: (item: CommandItem) => void }) {
  return (
    <Command.Item
      onSelect={() => onSelect(item)}
      className="flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] cursor-pointer text-[var(--text-primary)] hover:bg-[var(--bg-hover)] data-[selected=true]:bg-[var(--bg-hover)] transition-colors"
    >
      <span className="text-[var(--text-secondary)]">{item.icon}</span>
      <span className="flex-1">{item.title}</span>
      {item.shortcut && (
        <kbd className="px-2 py-0.5 text-xs text-[var(--text-muted)] bg-[var(--bg-subtle)] rounded">
          {item.shortcut}
        </kbd>
      )}
    </Command.Item>
  );
}
