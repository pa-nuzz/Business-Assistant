'use client';

import { useCallback, useRef } from 'react';

interface SoundEffectsOptions {
  enabled?: boolean;
  volume?: number;
}

class SoundEffects {
  private enabled: boolean;
  private volume: number;
  private audioContext: AudioContext | null = null;

  constructor(options: SoundEffectsOptions = {}) {
    this.enabled = options.enabled ?? true;
    this.volume = options.volume ?? 0.3;
  }

  private initAudioContext() {
    if (!this.audioContext && typeof window !== 'undefined') {
      this.audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    }
    return this.audioContext;
  }

  private playTone(
    frequency: number,
    duration: number,
    type: OscillatorType = 'sine',
    fadeOut: boolean = true
  ) {
    if (!this.enabled) return;

    const ctx = this.initAudioContext();
    if (!ctx) return;

    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);

    const vol = this.volume;
    gainNode.gain.setValueAtTime(0, ctx.currentTime);
    gainNode.gain.linearRampToValueAtTime(vol, ctx.currentTime + 0.01);

    if (fadeOut) {
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    }

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + duration);
  }

  // Gentle pop on send
  pop() {
    // Quick ascending blip
    this.playTone(800, 0.15, 'sine', true);
    setTimeout(() => this.playTone(1200, 0.1, 'sine', true), 50);
  }

  // Soft chime on receive
  chime() {
    // Pleasant bell-like sound
    this.playTone(523.25, 0.4, 'sine', true); // C5
    setTimeout(() => this.playTone(659.25, 0.3, 'sine', true), 100); // E5
    setTimeout(() => this.playTone(783.99, 0.5, 'sine', true), 200); // G5
  }

  // Success sound for task completion
  success() {
    // Triumphant ascending arpeggio
    this.playTone(523.25, 0.2, 'sine', true);
    setTimeout(() => this.playTone(659.25, 0.2, 'sine', true), 100);
    setTimeout(() => this.playTone(783.99, 0.2, 'sine', true), 200);
    setTimeout(() => this.playTone(1046.5, 0.6, 'sine', true), 300);
  }

  // Error sound
  error() {
    // Descending low tone
    this.playTone(200, 0.3, 'sawtooth', true);
    setTimeout(() => this.playTone(150, 0.4, 'sawtooth', true), 150);
  }

  // Toggle on/off
  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  setVolume(volume: number) {
    this.volume = Math.max(0, Math.min(1, volume));
  }
}

// Singleton instance
let soundEffectsInstance: SoundEffects | null = null;

export function getSoundEffects(options?: SoundEffectsOptions): SoundEffects {
  if (!soundEffectsInstance) {
    soundEffectsInstance = new SoundEffects(options);
  }
  return soundEffectsInstance;
}

// React hook for sound effects
export function useSoundEffects(options?: SoundEffectsOptions) {
  const soundRef = useRef<SoundEffects | null>(null);

  if (!soundRef.current) {
    soundRef.current = getSoundEffects(options);
  }

  const pop = useCallback(() => soundRef.current?.pop(), []);
  const chime = useCallback(() => soundRef.current?.chime(), []);
  const success = useCallback(() => soundRef.current?.success(), []);
  const error = useCallback(() => soundRef.current?.error(), []);
  const setEnabled = useCallback((enabled: boolean) => soundRef.current?.setEnabled(enabled), []);
  const setVolume = useCallback((volume: number) => soundRef.current?.setVolume(volume), []);

  return { pop, chime, success, error, setEnabled, setVolume };
}

export { SoundEffects };
