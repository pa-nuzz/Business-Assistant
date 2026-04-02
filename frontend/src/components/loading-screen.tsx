'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLoading } from './loading-context';

interface LoadingScreenProps {
  children: React.ReactNode;
}

export default function LoadingScreen({ children }: LoadingScreenProps) {
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const { isLoading: isAuthLoading } = useLoading();

  useEffect(() => {
    // Check if this is a hard reload using Navigation API
    // @ts-ignore - navigation is not in all browsers yet
    const navEntry = window.performance?.getEntriesByType?.('navigation')?.[0] as any;
    const navigationType = navEntry?.type;
    
    // 'reload' in new API, also check legacy performance.navigation.type === 1
    const isReload = navigationType === 'reload' || 
                     window.performance?.navigation?.type === 1 ||
                     !sessionStorage.getItem('app-loaded');
    
    if (isReload) {
      // Mark app as loaded for this session
      sessionStorage.setItem('app-loaded', 'true');
      // Show loading for initial load/reload
      const timer = setTimeout(() => {
        setIsInitialLoading(false);
      }, 1200);
      return () => clearTimeout(timer);
    } else {
      // Client-side navigation - skip loading screen immediately
      setIsInitialLoading(false);
    }
  }, []);

  const showLoading = isInitialLoading || isAuthLoading;

  return (
    <>
      <AnimatePresence mode="wait">
        {showLoading && (
          <motion.div
            key="loader"
            initial={{ opacity: 1 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-[9999] flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #dbeafe 0%, #eff6ff 50%, #e0f2fe 100%)' }}
          >
            <motion.div
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ 
                duration: 0.5, 
                ease: [0.34, 1.56, 0.64, 1]
              }}
              className="relative flex flex-col items-center"
            >
              {/* Logo with soft shadow */}
              <div className="relative">
                <motion.img
                  src="/logos/app-logo.svg"
                  alt="AEIOU AI"
                  className="w-20 h-20 object-contain drop-shadow-xl"
                  animate={{
                    y: [0, -4, 0],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
                {/* Subtle glow effect */}
                <div 
                  className="absolute inset-0 -z-10 blur-2xl opacity-40"
                  style={{ background: 'radial-gradient(circle, #3b82f6 0%, transparent 70%)' }}
                />
              </div>
              
              {/* App name */}
              <motion.p
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15, duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                className="mt-5 text-sm font-medium text-slate-600 tracking-wider uppercase"
              >
                AEIOU AI
              </motion.p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: showLoading ? 0 : 1 }}
        transition={{ duration: 0.3 }}
        style={{ visibility: showLoading ? 'hidden' : 'visible' }}
      >
        {children}
      </motion.div>
    </>
  );
}
