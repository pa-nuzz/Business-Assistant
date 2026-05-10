"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Mail, Lock, CheckCircle2, Loader2, ArrowLeft } from "lucide-react";
import { auth } from "@/lib/api";
import { toast } from "sonner";
import { AxiosApiError, getErrorMessage } from "@/types/errors";

import { AnimatedCharacters } from "@/components/ui/auth-animated-characters";

export default function AnimatedForgotPasswordPage() {
  const [step, setStep] = useState<'email' | 'code' | 'password' | 'success'>('email');
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const router = useRouter();

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim()) { setError("Please enter your email"); return; }
    setIsLoading(true);
    try {
      await auth.forgotPassword(email);
      toast.success("Reset code sent!");
      setStep('code');
    } catch (err: unknown) {
      const msg = (err as AxiosApiError).response?.data?.error || "";
      setError(msg.includes("not found") ? "No account with this email" : getErrorMessage(err as AxiosApiError));
    } finally { setIsLoading(false); }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (code.length !== 6) { setError("Enter 6-digit code"); return; }
    setIsLoading(true);
    try {
      await auth.verifyResetCode(email, code);
      toast.success("Code verified!");
      setStep('password');
    } catch { setError("Invalid or expired code"); }
    finally { setIsLoading(false); }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) { setError("Passwords don't match"); return; }
    if (newPassword.length < 8) { setError("Password must be 8+ characters"); return; }
    setIsLoading(true);
    try {
      const response = await auth.resetPassword(email, code, newPassword);
      toast.success(response.message || "Password updated!");
      setStep('success');
    } catch (err: unknown) {
      setError(getErrorMessage(err as AxiosApiError));
    } finally { setIsLoading(false); }
  };

  const handleResend = async () => {
    setIsLoading(true);
    try { await auth.forgotPassword(email); toast.success("New code sent!"); }
    catch { setError("Failed to resend"); }
    finally { setIsLoading(false); }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="relative hidden lg:flex flex-col justify-between bg-linear-to-br from-primary/90 via-primary to-primary/80 p-12 text-primary-foreground overflow-hidden">
        <div className="relative z-20 h-10" />
        <div className="relative z-20 flex items-end justify-center h-[500px]">
          <AnimatedCharacters isTyping={isTyping} showPassword={showPassword || showConfirmPassword} password={newPassword || confirmPassword} />
        </div>
        <div className="relative z-20 flex items-center gap-8 text-sm text-white/80">
          <Link href="/login" className="hover:text-white transition-colors flex items-center gap-2">
            <ArrowLeft className="size-4" />
            <span>Back to login</span>
          </Link>
        </div>
        <div className="absolute inset-0 grid-dna opacity-20" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl" />
      </div>

      <div className="flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-[420px]">


          {step === 'email' && (
            <>
              <div className="text-center mb-10">
                <h1 className="text-3xl font-bold tracking-tight mb-2 text-slate-900">Forgot password?</h1>
                <p className="text-slate-600 text-sm">Enter your email to get a reset code</p>
              </div>
              <form onSubmit={handleSendCode} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                  <div className="relative">
                    <Input id="email" type="email" placeholder="Enter your email" value={email} onChange={(e) => setEmail(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 pr-10 bg-background border-border/60 focus:border-primary" />
                    <Mail className="absolute right-3 top-1/2 -translate-y-1/2 size-5 text-slate-400" />
                  </div>
                </div>
                {error && <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">{typeof error === 'string' ? error : JSON.stringify(error)}</div>}
                <Button type="submit" className="w-full h-12 text-base font-medium" size="lg" disabled={isLoading}>
                  {isLoading ? <><Loader2 className="mr-2 size-4 animate-spin" />Sending...</> : "Send reset code"}
                </Button>
              </form>
            </>
          )}

          {step === 'code' && (
            <>
              <div className="text-center mb-10">
                <h1 className="text-3xl font-bold tracking-tight mb-2 text-slate-900">Enter code</h1>
                <p className="text-slate-600 text-sm">We sent a 6-digit code to <strong className="text-slate-900">{email}</strong></p>
              </div>
              <form onSubmit={handleVerifyCode} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="code" className="text-sm font-medium">Verification Code</Label>
                  <Input id="code" type="text" inputMode="numeric" maxLength={6} placeholder="000000" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 text-center text-2xl tracking-[0.5em] font-mono bg-background border-border/60 focus:border-primary" />
                </div>
                {error && <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">{typeof error === 'string' ? error : JSON.stringify(error)}</div>}
                <Button type="submit" className="w-full h-12 text-base font-medium" size="lg" disabled={isLoading || code.length !== 6}>
                  {isLoading ? <><Loader2 className="mr-2 size-4 animate-spin" />Verifying...</> : "Verify code"}
                </Button>
                <div className="text-center">
                  <button type="button" onClick={handleResend} disabled={isLoading} className="text-sm text-primary hover:underline disabled:opacity-50">Didn't receive it? Resend code</button>
                </div>
              </form>
            </>
          )}

          {step === 'password' && (
            <>
              <div className="text-center mb-10">
                <h1 className="text-3xl font-bold tracking-tight mb-2 text-slate-900">New password</h1>
                <p className="text-slate-600 text-sm">Create a new password for your account</p>
              </div>
              <form onSubmit={handleResetPassword} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="newPassword" className="text-sm font-medium">New Password</Label>
                  <div className="relative">
                    <Input id="newPassword" type={showPassword ? "text" : "password"} placeholder="Enter new password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required minLength={8} className="h-12 pr-10 bg-background border-border/60 focus:border-primary" />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors">
                      {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirm Password</Label>
                  <div className="relative">
                    <Input id="confirmPassword" type={showConfirmPassword ? "text" : "password"} placeholder="Confirm new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 pr-10 bg-background border-border/60 focus:border-primary" />
                    <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors">
                      {showConfirmPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                    </button>
                  </div>
                </div>
                {error && <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">{typeof error === 'string' ? error : JSON.stringify(error)}</div>}
                <Button type="submit" className="w-full h-12 text-base font-medium" size="lg" disabled={isLoading}>
                  {isLoading ? <><Loader2 className="mr-2 size-4 animate-spin" />Updating...</> : "Reset password"}
                </Button>
              </form>
            </>
          )}

          {step === 'success' && (
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-6">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight mb-3 text-slate-900">Password reset!</h1>
              <p className="text-slate-600 text-sm mb-6">Your password has been updated. You can now log in with your new password.</p>
              <Button className="w-full h-12" onClick={() => router.push('/login')}>
                <Lock className="mr-2 size-4" />Go to login
              </Button>
            </div>
          )}

          {step !== 'success' && (
            <div className="text-center text-sm text-slate-600 mt-8">
              Remember your password? <Link href="/login" className="text-slate-900 font-medium hover:underline">Sign in</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
