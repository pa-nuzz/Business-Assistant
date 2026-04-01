"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, ArrowLeft, Mail, KeyRound, CheckCircle2, Loader2 } from "lucide-react";
import { auth } from "@/lib/api";

// Rotating search rings
interface SearchRingProps {
  size: number;
  color: string;
  duration: number;
  delay: number;
  reverse?: boolean;
}

const SearchRing = ({ size, color, duration, delay, reverse }: SearchRingProps) => {
  return (
    <div 
      className="absolute rounded-full border-2"
      style={{ 
        width: size, 
        height: size, 
        borderColor: color,
        animation: `spin ${duration}s linear infinite ${delay}s`,
        animationDirection: reverse ? 'reverse' : 'normal',
      }}
    />
  );
};

// Pulsing key icon
interface PulsingKeyProps {
  isSearching: boolean;
}

const PulsingKey = ({ isSearching }: PulsingKeyProps) => {
  return (
    <div 
      className="relative flex items-center justify-center"
      style={{
        animation: isSearching ? 'pulse 1.5s ease-in-out infinite' : 'none',
      }}
    >
      <KeyRound className="w-20 h-20 text-white" strokeWidth={1.5} />
      
      {/* Animated rings around key */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div 
          className="absolute w-32 h-32 rounded-full border border-white/20"
          style={{ animation: 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite' }}
        />
        <div 
          className="absolute w-40 h-40 rounded-full border border-white/10"
          style={{ animation: 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite 0.5s' }}
        />
      </div>
    </div>
  );
};

// Floating particles
interface ParticleProps {
  size: number;
  delay: number;
  duration: number;
  startX: number;
  startY: number;
}

const Particle = ({ size, delay, duration, startX, startY }: ParticleProps) => {
  return (
    <div 
      className="absolute rounded-full bg-white/30"
      style={{
        width: size,
        height: size,
        left: startX,
        top: startY,
        animation: `float ${duration}s ease-in-out infinite ${delay}s`,
      }}
    />
  );
};

export default function AnimatedForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    if (!email.trim()) {
      setError("Please enter your email address");
      return;
    }

    setIsLoading(true);
    setIsSearching(true);

    try {
      // Simulate API call - replace with actual forgot password endpoint when available
      await new Promise(resolve => setTimeout(resolve, 2000));
      setIsSubmitted(true);
    } catch (err: any) {
      setError("Failed to send reset email. Please try again.");
    } finally {
      setIsLoading(false);
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Animation Section */}
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700 p-12 text-white overflow-hidden">
        {/* Floating particles */}
        <div className="absolute inset-0">
          <Particle size={6} delay={0} duration={8} startX={100} startY={150} />
          <Particle size={4} delay={1} duration={10} startX={800} startY={120} />
          <Particle size={8} delay={2} duration={7} startX={600} startY={600} />
          <Particle size={5} delay={3} duration={9} startX={300} startY={450} />
          <Particle size={3} delay={4} duration={11} startX={900} startY={300} />
          <Particle size={6} delay={5} duration={8} startX={150} startY={700} />
        </div>

        {/* Search rings animation */}
        <div className="absolute inset-0 flex items-center justify-center">
          <SearchRing size={200} color="rgba(255,255,255,0.1)" duration={20} delay={0} />
          <SearchRing size={280} color="rgba(255,255,255,0.08)" duration={25} delay={2} reverse />
          <SearchRing size={360} color="rgba(255,255,255,0.06)" duration={30} delay={4} />
        </div>

        {/* Top branding */}
        <div className="relative z-20">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <div className="size-8 rounded-lg bg-white/10 backdrop-blur-sm flex items-center justify-center">
              <Sparkles className="size-4" />
            </div>
            <span>AEIOU AI</span>
          </div>
        </div>

        {/* Center animation */}
        <div className="relative z-20 flex flex-col items-center justify-center">
          <PulsingKey isSearching={isSearching} />
          
          <div className="mt-12 text-center">
            <h2 className="text-2xl font-bold mb-2">
              {isSearching ? "Searching..." : "Password Recovery"}
            </h2>
            <p className="text-white/70 text-sm max-w-xs">
              {isSearching 
                ? "We're looking up your account..." 
                : "Don't worry, we'll help you get back in"}
            </p>
          </div>
        </div>

        {/* Bottom */}
        <div className="relative z-20">
          <Link 
            href="/login" 
            className="flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors"
          >
            <ArrowLeft className="size-4" />
            Back to login
          </Link>
        </div>

        {/* Decorative gradient */}
        <div className="absolute top-1/4 right-1/4 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-white/5 rounded-full blur-3xl" />

        {/* Custom animations */}
        <style jsx>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          @keyframes ping {
            75%, 100% {
              transform: scale(2);
              opacity: 0;
            }
          }
          @keyframes float {
            0%, 100% {
              transform: translateY(0) translateX(0);
              opacity: 0.3;
            }
            25% {
              transform: translateY(-20px) translateX(10px);
              opacity: 0.6;
            }
            50% {
              transform: translateY(10px) translateX(-10px);
              opacity: 0.4;
            }
            75% {
              transform: translateY(-10px) translateX(5px);
              opacity: 0.5;
            }
          }
          @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
          }
        `}</style>
      </div>

      {/* Right Form Section */}
      <div className="flex items-center justify-center p-8 bg-background overflow-y-auto">
        <div className="w-full max-w-[420px] py-8">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-8">
            <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="size-4 text-primary" />
            </div>
            <span>AEIOU AI</span>
          </div>

          {!isSubmitted ? (
            <>
              {/* Header */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-100 mb-4">
                  <Mail className="w-6 h-6 text-emerald-600" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">Forgot password?</h1>
                <p className="text-muted-foreground text-sm">
                  No worries! Enter your email and we'll send you a reset link.
                </p>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">Email address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    autoComplete="email"
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={() => setIsSearching(true)}
                    onBlur={() => setIsSearching(false)}
                    required
                    className="h-11 bg-background border-border/60 focus:border-primary"
                  />
                </div>

                {error && (
                  <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">
                    {error}
                  </div>
                )}

                <Button 
                  type="submit" 
                  className="w-full h-11 text-base font-medium bg-emerald-600 hover:bg-emerald-700" 
                  size="lg" 
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 size-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    "Send reset link"
                  )}
                </Button>
              </form>

              {/* Back to login */}
              <div className="text-center text-sm text-muted-foreground mt-6">
                Remember your password?{" "}
                <Link href="/login" className="text-emerald-600 font-medium hover:underline">
                  Sign in
                </Link>
              </div>
            </>
          ) : (
            /* Success State */
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 mb-6">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight mb-3">Check your email</h1>
              <p className="text-muted-foreground text-sm mb-6">
                We've sent a password reset link to <strong>{email}</strong>. 
                Please check your inbox and follow the instructions.
              </p>
              <div className="space-y-3">
                <Button 
                  variant="outline"
                  className="w-full"
                  onClick={() => setIsSubmitted(false)}
                >
                  Didn't receive it? Resend
                </Button>
                <Link href="/login">
                  <Button 
                    variant="ghost" 
                    className="w-full text-emerald-600"
                  >
                    Back to login
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
