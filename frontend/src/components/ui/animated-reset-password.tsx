"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, ArrowLeft, Lock, ShieldCheck, Eye, EyeOff, Loader2 } from "lucide-react";

// Shield with checkmark animation
interface ShieldProps {
  isSuccess: boolean;
}

const AnimatedShield = ({ isSuccess }: ShieldProps) => {
  return (
    <div className="relative flex items-center justify-center">
      <div 
        className={`transition-all duration-500 ${isSuccess ? 'scale-110' : 'scale-100'}`}
      >
        {isSuccess ? (
          <ShieldCheck className="w-20 h-20 text-white" strokeWidth={1.5} />
        ) : (
          <Lock className="w-20 h-20 text-white" strokeWidth={1.5} />
        )}
      </div>
      
      {/* Animated rings */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div 
          className="absolute w-32 h-32 rounded-full border-2 border-white/20"
          style={{ animation: 'spin 15s linear infinite' }}
        />
        <div 
          className="absolute w-40 h-40 rounded-full border border-white/10"
          style={{ animation: 'spin 20s linear infinite reverse' }}
        />
      </div>
    </div>
  );
};

// Password strength indicator bars
interface StrengthBarsProps {
  password: string;
}

const StrengthBars = ({ password }: StrengthBarsProps) => {
  const getStrength = (pwd: string) => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    return score;
  };

  const strength = getStrength(password);
  const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500', 'bg-emerald-500'];

  return (
    <div className="flex gap-1 mt-2">
      {[0, 1, 2, 3, 4].map((i) => (
        <div 
          key={i}
          className={`h-1 flex-1 rounded-full transition-all duration-300 ${
            i < strength ? colors[strength - 1] : 'bg-white/20'
          }`}
        />
      ))}
    </div>
  );
};

export default function AnimatedResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [passwordData, setPasswordData] = useState({
    newPassword: '',
    confirmPassword: '',
  });

  // Get uid and token from URL
  const uid = searchParams.get('uid');
  const token = searchParams.get('token');

  useEffect(() => {
    if (!uid || !token) {
      setError('Invalid or missing reset link. Please request a new password reset.');
    }
  }, [uid, token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!uid || !token) {
      setError('Invalid reset link. Please request a new one.');
      return;
    }

    if (!passwordData.newPassword || !passwordData.confirmPassword) {
      setError('Both password fields are required');
      return;
    }

    if (passwordData.newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      // Simulate API call - replace with actual reset password endpoint
      await new Promise(resolve => setTimeout(resolve, 1500));
      setSuccess(true);
      
      // Redirect after success
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    } catch (err: any) {
      setError('Failed to reset password. The link may have expired.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Animation Section */}
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-indigo-600 via-blue-600 to-sky-700 p-12 text-white overflow-hidden">
        {/* Animated background shapes */}
        <div className="absolute inset-0">
          <div 
            className="absolute top-20 left-20 w-40 h-40 bg-white/5 rounded-full blur-2xl"
            style={{ animation: 'pulse 4s ease-in-out infinite' }}
          />
          <div 
            className="absolute bottom-40 right-20 w-60 h-60 bg-white/5 rounded-full blur-3xl"
            style={{ animation: 'pulse 4s ease-in-out infinite 2s' }}
          />
        </div>

        {/* Top branding */}
        <div className="relative z-20">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden bg-gradient-to-br from-blue-500 to-blue-700">
              <img src="/logos/app-logo.svg" alt="AEIOU AI" className="w-full h-full object-contain" />
            </div>
            <span>AEIOU AI</span>
          </div>
        </div>

        {/* Center animation */}
        <div className="relative z-20 flex flex-col items-center justify-center">
          <AnimatedShield isSuccess={success} />
          
          <div className="mt-12 text-center">
            <h2 className="text-2xl font-bold mb-2">
              {success ? 'Password Reset!' : 'Secure Your Account'}
            </h2>
            <p className="text-white/70 text-sm max-w-xs">
              {success 
                ? 'Your password has been successfully reset.'
                : 'Create a strong password to protect your account.'}
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

        {/* Custom animations */}
        <style jsx>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          @keyframes pulse {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.1); }
          }
        `}</style>
      </div>

      {/* Right Form Section */}
      <div className="flex items-center justify-center p-8 bg-background overflow-y-auto">
        <div className="w-full max-w-[420px] py-8">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-8">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden bg-gradient-to-br from-blue-500 to-blue-700">
              <img src="/logos/app-logo.svg" alt="AEIOU AI" className="w-full h-full object-contain" />
            </div>
            <span>AEIOU AI</span>
          </div>

          {!success ? (
            <>
              {/* Header */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-100 mb-4">
                  <Lock className="w-6 h-6 text-indigo-600" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight mb-2 text-slate-900">Reset your password</h1>
                <p className="text-slate-600 text-sm">
                  Enter your new password below
                </p>
              </div>

              {/* Error for invalid link */}
              {error && error.includes('Invalid') && (
                <div className="p-4 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg mb-6">
                  {error}
                </div>
              )}

              {/* Form */}
              {!error.includes('Invalid') && (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="newPassword" className="text-sm font-medium">New Password</Label>
                    <div className="relative">
                      <Input
                        id="newPassword"
                        type={showPassword ? "text" : "password"}
                        placeholder="Create a strong password"
                        value={passwordData.newPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                        required
                        className="h-11 pr-10 bg-background border-border/60 focus:border-primary"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                      >
                        {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                      </button>
                    </div>
                    <StrengthBars password={passwordData.newPassword} />
                    <p className="text-xs text-slate-500">
                      Must be at least 8 characters with uppercase, number, and special character
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirm Password</Label>
                    <div className="relative">
                      <Input
                        id="confirmPassword"
                        type={showConfirmPassword ? "text" : "password"}
                        placeholder="Confirm your password"
                        value={passwordData.confirmPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                        required
                        className="h-11 pr-10 bg-background border-border/60 focus:border-primary"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                      >
                        {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                      </button>
                    </div>
                  </div>

                  {error && !error.includes('Invalid') && (
                    <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">
                      {error}
                    </div>
                  )}

                  <Button 
                    type="submit" 
                    className="w-full h-11 text-base font-medium bg-indigo-600 hover:bg-indigo-700" 
                    size="lg" 
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 size-4 animate-spin" />
                        Resetting...
                      </>
                    ) : (
                      "Reset Password"
                    )}
                  </Button>
                </form>
              )}

              {/* Back to login */}
              <div className="text-center text-sm text-slate-600 mt-6">
                <Link href="/login" className="text-indigo-600 font-medium hover:underline">
                  Back to login
                </Link>
              </div>
            </>
          ) : (
            /* Success State */
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-100 mb-6">
                <ShieldCheck className="w-8 h-8 text-indigo-600" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight mb-3 text-slate-900">Password Reset Complete!</h1>
              <p className="text-slate-600 text-sm mb-6">
                Your password has been successfully reset. You&apos;ll be redirected to the login page shortly.
              </p>
              <Button 
                className="w-full bg-indigo-600 hover:bg-indigo-700"
                onClick={() => router.push('/login')}
              >
                Go to Login
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
