'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface LoadingScreenProps {
  onComplete?: () => void;
  minDuration?: number;
}

// Animated equalizer bar component
const EqualizerBar = ({ delay, height }: { delay: number; height: number }) => (
  <motion.div
    className="w-1.5 bg-gradient-to-t from-blue-500 to-cyan-400 rounded-full"
    initial={{ height: 4 }}
    animate={{ height: [4, height, 4] }}
    transition={{
      duration: 0.6,
      repeat: Infinity,
      repeatType: 'reverse',
      delay: delay,
      ease: 'easeInOut',
    }}
  />
);

export default function LoadingScreen({ onComplete, minDuration = 2000 }: LoadingScreenProps) {
  const [hidden, setHidden] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Animate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + 2;
      });
    }, 40);

    // Hide after min duration
    const timer = setTimeout(() => {
      setHidden(true);
      onComplete?.();
    }, minDuration);

    return () => {
      clearTimeout(timer);
      clearInterval(progressInterval);
    };
  }, [minDuration, onComplete]);

  if (hidden) return null;

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-gradient-to-br from-white via-blue-50/30 to-white"
    >
      {/* Logo with glow effect */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative mb-8"
      >
        {/* Outer glow rings */}
        <motion.div
          className="absolute inset-0 rounded-full bg-blue-400/20 blur-2xl"
          animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute inset-2 rounded-full bg-cyan-400/20 blur-xl"
          animate={{ scale: [1.2, 1, 1.2], opacity: [0.2, 0.5, 0.2] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
        />
        
        {/* Logo */}
        <div className="relative w-24 h-24">
          <img
            src="/logos/core.svg"
            alt="AEIOU AI"
            className="w-full h-full object-contain drop-shadow-2xl"
          />
        </div>
      </motion.div>

      {/* Energetic equalizer */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.4 }}
        className="flex items-end gap-1 h-12 mb-6"
      >
        <EqualizerBar delay={0} height={32} />
        <EqualizerBar delay={0.1} height={48} />
        <EqualizerBar delay={0.2} height={24} />
        <EqualizerBar delay={0.15} height={40} />
        <EqualizerBar delay={0.05} height={28} />
        <EqualizerBar delay={0.25} height={44} />
        <EqualizerBar delay={0.1} height={36} />
        <EqualizerBar delay={0.2} height={20} />
        <EqualizerBar delay={0.05} height={32} />
        <EqualizerBar delay={0.15} height={48} />
        <EqualizerBar delay={0.1} height={28} />
        <EqualizerBar delay={0.2} height={40} />
      </motion.div>

      {/* Loading text with pulse */}
      <motion.p
        className="text-sm font-medium text-blue-600/80 mb-4"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        Initializing AEIOU AI...
      </motion.p>

      {/* Progress bar */}
      <div className="w-48 h-1 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 via-cyan-400 to-blue-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.1, ease: 'linear' }}
        />
      </div>

      {/* Percentage */}
      <motion.p
        className="text-xs text-gray-400 mt-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        {progress}%
      </motion.p>
    </motion.div>
  );
}
