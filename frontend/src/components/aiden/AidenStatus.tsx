'use client';

import { motion } from 'framer-motion';
import { AidenAvatar } from './AidenAvatar';

interface AidenStatusProps {
  status?: 'online' | 'thinking' | 'typing' | 'offline';
  message?: string;
}

const statusConfig = {
  online: { color: '#00E5A0', message: 'Aiden is ready' },
  thinking: { color: '#F5A623', message: 'Aiden is thinking...' },
  typing: { color: '#6C63FF', message: 'Aiden is typing...' },
  offline: { color: '#4A4A6A', message: 'Aiden is offline' },
};

export function AidenStatus({ status = 'online', message }: AidenStatusProps) {
  const config = statusConfig[status];
  const displayMessage = message || config.message;

  return (
    <div className="flex items-center gap-3 px-4 py-2 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)]">
      <AidenAvatar size="sm" animated={status === 'online'} showGlow={status === 'online'} />
      
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-[var(--text-primary)]">
          {displayMessage}
        </span>
        
        {/* Status indicator dot */}
        <motion.div
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: config.color }}
          animate={status === 'thinking' ? {
            scale: [1, 1.2, 1],
            opacity: [0.7, 1, 0.7],
          } : {}}
          transition={{ duration: 1, repeat: Infinity }}
        />
      </div>
    </div>
  );
}
