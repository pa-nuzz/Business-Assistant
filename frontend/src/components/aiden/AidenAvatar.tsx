'use client';

import { motion } from 'framer-motion';

interface AidenAvatarProps {
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  showGlow?: boolean;
}

const sizes = {
  sm: { container: 32, letter: 16 },
  md: { container: 40, letter: 20 },
  lg: { container: 64, letter: 32 },
};

export function AidenAvatar({ size = 'md', animated = true, showGlow = false }: AidenAvatarProps) {
  const { container, letter } = sizes[size];

  return (
    <motion.div
      className="relative flex items-center justify-center rounded-full"
      style={{
        width: container,
        height: container,
        background: 'linear-gradient(135deg, var(--brand-primary) 0%, #8B84FF 100%)',
        boxShadow: showGlow ? 'var(--shadow-glow)' : undefined,
      }}
      whileHover={animated ? { scale: 1.05 } : undefined}
      whileTap={animated ? { scale: 0.95 } : undefined}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Pulsing ring for "online" indicator */}
      {animated && (
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            background: 'var(--brand-primary)',
          }}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.4, 0, 0.4],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}
      
      {/* A monogram */}
      <span
        className="font-bold text-white relative z-10"
        style={{
          fontSize: letter,
          fontFamily: 'var(--font-display)',
        }}
      >
        A
      </span>
    </motion.div>
  );
}
