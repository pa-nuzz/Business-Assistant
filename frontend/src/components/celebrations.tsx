'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';

interface CelebrationOptions {
  particleCount?: number;
  spread?: number;
  origin?: { x: number; y: number };
  colors?: string[];
  disableForReducedMotion?: boolean;
}

const defaultColors = ['#3B82F6', '#60A5FA', '#2DD4BF', '#6366F1', '#93C5FD'];

export function triggerConfetti(options: CelebrationOptions = {}) {
  const {
    particleCount = 80,
    spread = 70,
    origin = { x: 0.5, y: 0.6 },
    colors = defaultColors,
    disableForReducedMotion = true,
  } = options;

  // Respect reduced motion preference
  if (disableForReducedMotion && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  // Left burst
  confetti({
    particleCount: Math.floor(particleCount / 2),
    spread,
    origin: { x: origin.x - 0.2, y: origin.y },
    colors,
    gravity: 0.8,
    scalar: 0.9,
    drift: -1,
  });

  // Right burst
  confetti({
    particleCount: Math.floor(particleCount / 2),
    spread,
    origin: { x: origin.x + 0.2, y: origin.y },
    colors,
    gravity: 0.8,
    scalar: 0.9,
    drift: 1,
  });
}

// Mini confetti for smaller celebrations
export function triggerMiniConfetti(origin?: { x: number; y: number }) {
  triggerConfetti({
    particleCount: 40,
    spread: 50,
    origin: origin || { x: 0.5, y: 0.7 },
    colors: defaultColors,
  });
}

// Animated checkmark component
interface CheckmarkAnimationProps {
  size?: number;
  className?: string;
  onComplete?: () => void;
  duration?: number;
}

export function CheckmarkAnimation({
  size = 48,
  className = '',
  onComplete,
  duration = 0.6,
}: CheckmarkAnimationProps) {
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 52 52"
      className={className}
      initial="hidden"
      animate="visible"
      onAnimationComplete={onComplete}
    >
      {/* Circle background */}
      <motion.circle
        cx="26"
        cy="26"
        r="24"
        fill="#3B82F6"
        variants={{
          hidden: { scale: 0, opacity: 0 },
          visible: {
            scale: 1,
            opacity: 1,
            transition: { duration: duration * 0.4, ease: 'easeOut' },
          },
        }}
      />

      {/* Checkmark path */}
      <motion.path
        fill="none"
        stroke="#FFFFFF"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M14 27 L22 35 L38 19"
        variants={{
          hidden: { pathLength: 0, opacity: 0 },
          visible: {
            pathLength: 1,
            opacity: 1,
            transition: {
              pathLength: { duration: duration * 0.5, delay: duration * 0.3, ease: 'easeOut' },
              opacity: { duration: 0.1 },
            },
          },
        }}
      />

      {/* Pulse ring effect */}
      <motion.circle
        cx="26"
        cy="26"
        r="24"
        fill="none"
        stroke="#3B82F6"
        strokeWidth="2"
        variants={{
          hidden: { scale: 1, opacity: 0 },
          visible: {
            scale: 1.5,
            opacity: [0.5, 0],
            transition: {
              delay: duration * 0.6,
              duration: duration * 0.4,
              ease: 'easeOut',
            },
          },
        }}
      />
    </motion.svg>
  );
}

// Success toast with confetti
interface SuccessCelebrationProps {
  message?: string;
  showConfetti?: boolean;
  onClose?: () => void;
  duration?: number;
}

export function SuccessCelebration({
  message = 'Success!',
  showConfetti = true,
  onClose,
  duration = 2000,
}: SuccessCelebrationProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (showConfetti) {
      triggerMiniConfetti();
    }

    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => onClose?.(), 300);
    }, duration);

    return () => clearTimeout(timer);
  }, [showConfetti, onClose, duration]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8, y: -20 }}
          className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 flex flex-col items-center gap-4"
        >
          <CheckmarkAnimation size={64} />
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-lg font-semibold text-gray-800"
          >
            {message}
          </motion.p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Hook for task completion celebrations
export function useCelebration() {
  const celebrate = useCallback((options?: CelebrationOptions) => {
    triggerConfetti(options);
  }, []);

  const celebrateMini = useCallback((origin?: { x: number; y: number }) => {
    triggerMiniConfetti(origin);
  }, []);

  return { celebrate, celebrateMini, triggerConfetti, triggerMiniConfetti };
}
