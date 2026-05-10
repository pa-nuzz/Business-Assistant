"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, ArrowLeft } from "lucide-react";
import { auth } from "@/lib/api";
import { toast } from "sonner";
import { AxiosApiError } from "@/types/errors";
import { AnimatedLogo } from "@/components/ui/animated-logo";
import Link from "next/link";

import { AnimatedCharacters } from "@/components/ui/auth-animated-characters";

export default function AnimatedSignupPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) { setError("Passwords don't match."); return; }
    if (!agreedToTerms) { setError("Please agree to terms."); return; }
    setIsLoading(true);
    try {
      const response = await auth.register(username.trim(), password, email);
      toast.success('Registration successful! Verify email.');
      router.push(`/verify-email?username=${encodeURIComponent(response.username)}`);
    } catch (err: any) {
      const apiError = err as AxiosApiError;
      setError(apiError.response?.data?.detail || "Registration failed.");
    } finally { setIsLoading(false); }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="relative hidden lg:flex flex-col justify-between bg-primary p-12 text-primary-foreground overflow-hidden">
        <div className="relative z-20 h-10" />

        <div className="relative z-20 flex items-end justify-center h-[500px]">
          <AnimatedCharacters 
            isTyping={isTyping} 
            password={password} 
            showPassword={showPassword || showConfirmPassword} 
          />
        </div>

        <div className="relative z-20 flex items-center gap-8 text-sm text-white/80">
          <Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
          <Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link>
        </div>
        <div className="absolute inset-0 grid-dna opacity-20" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl" />
      </div>

      {/* Form on Right */}
      <div className="flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-[420px]">
          <Link href="/" className="inline-flex items-center gap-2 text-slate-400 hover:text-slate-900 transition-colors mb-8 text-sm font-bold uppercase tracking-widest">
            <ArrowLeft className="w-4 h-4" />
            Back Home
          </Link>
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold tracking-tight mb-2">Create account</h1>
            <p className="text-muted-foreground text-sm">Join us and get started today</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2"><Label htmlFor="username" className="text-sm font-bold text-slate-400 uppercase tracking-widest">Username</Label><Input id="username" placeholder="Choose a username" value={username} onChange={(e) => setUsername(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 bg-background border-border/60" /></div>
            <div className="space-y-2"><Label htmlFor="email" className="text-sm font-bold text-slate-400 uppercase tracking-widest">Email</Label><Input id="email" type="email" placeholder="Enter your email" value={email} onChange={(e) => setEmail(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 bg-background border-border/60" /></div>
            
            <div className="space-y-2">
              <Label htmlFor="password" title="Password" className="text-sm font-bold text-slate-400 uppercase tracking-widest">Password</Label>
              <div className="relative">
                <Input id="password" type={showPassword ? "text" : "password"} placeholder="Create a password" value={password} onChange={(e) => setPassword(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 bg-background border-border/60 pr-10" />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors">
                  {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm" className="text-sm font-bold text-slate-400 uppercase tracking-widest">Confirm Password</Label>
              <div className="relative">
                <Input id="confirm" type={showConfirmPassword ? "text" : "password"} placeholder="Confirm your password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 bg-background border-border/60 pr-10" />
                <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors">
                  {showConfirmPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-start space-x-2"><Checkbox id="terms" checked={agreedToTerms} onCheckedChange={(c) => setAgreedToTerms(c as boolean)} /><Label htmlFor="terms" className="text-sm font-normal cursor-pointer leading-normal">I agree to the <Link href="/terms" className="text-indigo-600 font-bold hover:underline">Terms</Link> and <Link href="/privacy" className="text-indigo-600 font-bold hover:underline">Privacy</Link></Label></div>
            {error && <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">{error}</div>}
            <Button type="submit" className="w-full h-12 text-base font-medium bg-indigo-600 hover:bg-indigo-700 shadow-lg" size="lg" disabled={isLoading}>{isLoading ? "Creating account..." : "Sign up"}</Button>
          </form>
          <div className="text-center text-sm text-muted-foreground mt-8">Already have an account? <Link href="/login" className="text-indigo-600 font-bold hover:underline">Log in</Link></div>
        </div>
      </div>
    </div>
  );
}
