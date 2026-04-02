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

interface PupilProps {
  size?: number;
  maxDistance?: number;
  pupilColor?: string;
  forceLookX?: number;
  forceLookY?: number;
}

const Pupil = ({ 
  size = 12, 
  maxDistance = 5,
  pupilColor = "black",
  forceLookX,
  forceLookY
}: PupilProps) => {
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const pupilRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const calculatePupilPosition = () => {
    if (!pupilRef.current) return { x: 0, y: 0 };
    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }
    const pupil = pupilRef.current.getBoundingClientRect();
    const pupilCenterX = pupil.left + pupil.width / 2;
    const pupilCenterY = pupil.top + pupil.height / 2;
    const deltaX = mouseX - pupilCenterX;
    const deltaY = mouseY - pupilCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);
    const angle = Math.atan2(deltaY, deltaX);
    return { x: Math.cos(angle) * distance, y: Math.sin(angle) * distance };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={pupilRef}
      className="rounded-full"
      style={{
        width: `${size}px`,
        height: `${size}px`,
        backgroundColor: pupilColor,
        transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
        transition: 'transform 0.1s ease-out',
      }}
    />
  );
};

interface EyeBallProps {
  size?: number;
  pupilSize?: number;
  maxDistance?: number;
  eyeColor?: string;
  pupilColor?: string;
  isBlinking?: boolean;
  forceLookX?: number;
  forceLookY?: number;
}

const EyeBall = ({ 
  size = 48, 
  pupilSize = 16, 
  maxDistance = 10,
  eyeColor = "white",
  pupilColor = "black",
  isBlinking = false,
  forceLookX,
  forceLookY
}: EyeBallProps) => {
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const eyeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const calculatePupilPosition = () => {
    if (!eyeRef.current) return { x: 0, y: 0 };
    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }
    const eye = eyeRef.current.getBoundingClientRect();
    const eyeCenterX = eye.left + eye.width / 2;
    const eyeCenterY = eye.top + eye.height / 2;
    const deltaX = mouseX - eyeCenterX;
    const deltaY = mouseY - eyeCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);
    const angle = Math.atan2(deltaY, deltaX);
    return { x: Math.cos(angle) * distance, y: Math.sin(angle) * distance };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={eyeRef}
      className="rounded-full flex items-center justify-center transition-all duration-150"
      style={{
        width: `${size}px`,
        height: isBlinking ? '2px' : `${size}px`,
        backgroundColor: eyeColor,
        overflow: 'hidden',
      }}
    >
      {!isBlinking && (
        <div
          className="rounded-full"
          style={{
            width: `${pupilSize}px`,
            height: `${pupilSize}px`,
            backgroundColor: pupilColor,
            transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
            transition: 'transform 0.1s ease-out',
          }}
        />
      )}
    </div>
  );
};

function AnimatedCharacters({ isTyping, showPassword, password }: { isTyping: boolean; showPassword: boolean; password: string }) {
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);
  const [isPurpleBlinking, setIsPurpleBlinking] = useState(false);
  const [isBlackBlinking, setIsBlackBlinking] = useState(false);
  const [isLookingAtEachOther, setIsLookingAtEachOther] = useState(false);
  const [isPurplePeeking, setIsPurplePeeking] = useState(false);
  const purpleRef = useRef<HTMLDivElement>(null);
  const blackRef = useRef<HTMLDivElement>(null);
  const yellowRef = useRef<HTMLDivElement>(null);
  const orangeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;
    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsPurpleBlinking(true);
        setTimeout(() => { setIsPurpleBlinking(false); scheduleBlink(); }, 150);
      }, getRandomBlinkInterval());
      return blinkTimeout;
    };
    const timeout = scheduleBlink();
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;
    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsBlackBlinking(true);
        setTimeout(() => { setIsBlackBlinking(false); scheduleBlink(); }, 150);
      }, getRandomBlinkInterval());
      return blinkTimeout;
    };
    const timeout = scheduleBlink();
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (isTyping) {
      setIsLookingAtEachOther(true);
      const timer = setTimeout(() => setIsLookingAtEachOther(false), 800);
      return () => clearTimeout(timer);
    }
  }, [isTyping]);

  useEffect(() => {
    if (password.length > 0 && showPassword) {
      const schedulePeek = () => {
        const peekInterval = setTimeout(() => {
          setIsPurplePeeking(true);
          setTimeout(() => setIsPurplePeeking(false), 800);
        }, Math.random() * 3000 + 2000);
        return peekInterval;
      };
      const firstPeek = schedulePeek();
      return () => clearTimeout(firstPeek);
    } else {
      setIsPurplePeeking(false);
    }
  }, [password, showPassword]);

  const calculatePosition = (ref: React.RefObject<HTMLDivElement | null>) => {
    if (!ref.current) return { faceX: 0, faceY: 0, bodySkew: 0 };
    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 3;
    const deltaX = mouseX - centerX;
    const deltaY = mouseY - centerY;
    return {
      faceX: Math.max(-15, Math.min(15, deltaX / 20)),
      faceY: Math.max(-10, Math.min(10, deltaY / 30)),
      bodySkew: Math.max(-6, Math.min(6, -deltaX / 120))
    };
  };

  const purplePos = calculatePosition(purpleRef);
  const blackPos = calculatePosition(blackRef);
  const yellowPos = calculatePosition(yellowRef);
  const orangePos = calculatePosition(orangeRef);

  const isAnyPasswordVisible = password.length > 0 && showPassword;
  const isAnyPasswordHidden = password.length > 0 && !showPassword;

  return (
    <div className="relative" style={{ width: '550px', height: '400px' }}>
      <div ref={purpleRef} className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{ left: '70px', width: '180px', height: (isTyping || isAnyPasswordHidden) ? '440px' : '400px', backgroundColor: '#6C3FF5', borderRadius: '10px 10px 0 0', zIndex: 1, transform: isAnyPasswordVisible ? 'skewX(0deg)' : (isTyping || isAnyPasswordHidden) ? `skewX(${(purplePos.bodySkew || 0) - 12}deg) translateX(40px)` : `skewX(${purplePos.bodySkew || 0}deg)`, transformOrigin: 'bottom center' }}>
        <div className="absolute flex gap-8 transition-all duration-700 ease-in-out"
          style={{ left: isAnyPasswordVisible ? '20px' : isLookingAtEachOther ? '55px' : `${45 + purplePos.faceX}px`, top: isAnyPasswordVisible ? '35px' : isLookingAtEachOther ? '65px' : `${40 + purplePos.faceY}px` }}>
          <EyeBall size={18} pupilSize={7} maxDistance={5} eyeColor="white" pupilColor="#2D2D2D" isBlinking={isPurpleBlinking} forceLookX={isAnyPasswordVisible ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined} forceLookY={isAnyPasswordVisible ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined} />
          <EyeBall size={18} pupilSize={7} maxDistance={5} eyeColor="white" pupilColor="#2D2D2D" isBlinking={isPurpleBlinking} forceLookX={isAnyPasswordVisible ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined} forceLookY={isAnyPasswordVisible ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined} />
        </div>
      </div>
      <div ref={blackRef} className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{ left: '240px', width: '120px', height: '310px', backgroundColor: '#2D2D2D', borderRadius: '8px 8px 0 0', zIndex: 2, transform: isAnyPasswordVisible ? 'skewX(0deg)' : isLookingAtEachOther ? `skewX(${(blackPos.bodySkew || 0) * 1.5 + 10}deg) translateX(20px)` : (isTyping || isAnyPasswordHidden) ? `skewX(${(blackPos.bodySkew || 0) * 1.5}deg)` : `skewX(${blackPos.bodySkew || 0}deg)`, transformOrigin: 'bottom center' }}>
        <div className="absolute flex gap-6 transition-all duration-700 ease-in-out"
          style={{ left: isAnyPasswordVisible ? '10px' : isLookingAtEachOther ? '32px' : `${26 + blackPos.faceX}px`, top: isAnyPasswordVisible ? '28px' : isLookingAtEachOther ? '12px' : `${32 + blackPos.faceY}px` }}>
          <EyeBall size={16} pupilSize={6} maxDistance={4} eyeColor="white" pupilColor="#2D2D2D" isBlinking={isBlackBlinking} forceLookX={isAnyPasswordVisible ? -4 : isLookingAtEachOther ? 0 : undefined} forceLookY={isAnyPasswordVisible ? -4 : isLookingAtEachOther ? -4 : undefined} />
          <EyeBall size={16} pupilSize={6} maxDistance={4} eyeColor="white" pupilColor="#2D2D2D" isBlinking={isBlackBlinking} forceLookX={isAnyPasswordVisible ? -4 : isLookingAtEachOther ? 0 : undefined} forceLookY={isAnyPasswordVisible ? -4 : isLookingAtEachOther ? -4 : undefined} />
        </div>
      </div>
      <div ref={orangeRef} className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{ left: '0px', width: '240px', height: '200px', zIndex: 3, backgroundColor: '#FF9B6B', borderRadius: '120px 120px 0 0', transform: isAnyPasswordVisible ? 'skewX(0deg)' : `skewX(${orangePos.bodySkew || 0}deg)`, transformOrigin: 'bottom center' }}>
        <div className="absolute flex gap-8 transition-all duration-200 ease-out"
          style={{ left: isAnyPasswordVisible ? '50px' : `${82 + (orangePos.faceX || 0)}px`, top: isAnyPasswordVisible ? '85px' : `${90 + (orangePos.faceY || 0)}px` }}>
          <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isAnyPasswordVisible ? -5 : undefined} forceLookY={isAnyPasswordVisible ? -4 : undefined} />
          <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isAnyPasswordVisible ? -5 : undefined} forceLookY={isAnyPasswordVisible ? -4 : undefined} />
        </div>
      </div>
      <div ref={yellowRef} className="absolute bottom-0 transition-all duration-700 ease-in-out"
        style={{ left: '310px', width: '140px', height: '230px', backgroundColor: '#E8D754', borderRadius: '70px 70px 0 0', zIndex: 4, transform: isAnyPasswordVisible ? 'skewX(0deg)' : `skewX(${yellowPos.bodySkew || 0}deg)`, transformOrigin: 'bottom center' }}>
        <div className="absolute flex gap-6 transition-all duration-200 ease-out"
          style={{ left: isAnyPasswordVisible ? '20px' : `${52 + (yellowPos.faceX || 0)}px`, top: isAnyPasswordVisible ? '35px' : `${40 + (yellowPos.faceY || 0)}px` }}>
          <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isAnyPasswordVisible ? -5 : undefined} forceLookY={isAnyPasswordVisible ? -4 : undefined} />
          <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={isAnyPasswordVisible ? -5 : undefined} forceLookY={isAnyPasswordVisible ? -4 : undefined} />
        </div>
        <div className="absolute w-20 h-[4px] bg-[#2D2D2D] rounded-full transition-all duration-200 ease-out"
          style={{ left: isAnyPasswordVisible ? '10px' : `${40 + (yellowPos.faceY || 0)}px`, top: isAnyPasswordVisible ? '88px' : `${88 + (yellowPos.faceY || 0)}px` }} />
      </div>
    </div>
  );
}

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
    } catch (err: any) {
      const msg = err.response?.data?.error || "";
      setError(msg.includes("not found") ? "No account with this email" : "Failed to send code");
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
    } catch (err: any) {
      let msg = err.response?.data?.error || err.response?.data?.message || "Failed to reset password";
      if (typeof msg !== 'string') msg = JSON.stringify(msg);
      setError(msg);
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
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary/90 via-primary to-primary/80 p-12 text-primary-foreground overflow-hidden">
        <div className="relative z-20">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <img src="/logos/app-logo.svg" alt="AEIOU AI" className="w-8 h-8" />
            <span>AEIOU AI</span>
          </div>
        </div>
        <div className="relative z-20 flex items-end justify-center h-[500px]">
          <AnimatedCharacters isTyping={isTyping} showPassword={showPassword || showConfirmPassword} password={newPassword || confirmPassword} />
        </div>
        <div className="relative z-20 flex items-center gap-8 text-sm text-white/80">
          <Link href="/login" className="hover:text-white transition-colors flex items-center gap-2">
            <ArrowLeft className="size-4" />
            <span>Back to login</span>
          </Link>
        </div>
        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl" />
      </div>

      <div className="flex items-center justify-center p-8" style={{ background: 'linear-gradient(135deg, #dbeafe 0%, #eff6ff 50%, #e0f2fe 100%)' }}>
        <div className="w-full max-w-[420px]">
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12">
            <img src="/logos/app-logo.svg" alt="AEIOU AI" className="w-8 h-8" />
            <span>AEIOU AI</span>
          </div>

          {step === 'email' && (
            <>
              <div className="text-center mb-10">
                <h1 className="text-3xl font-bold tracking-tight mb-2">Forgot password?</h1>
                <p className="text-muted-foreground text-sm">Enter your email to get a reset code</p>
              </div>
              <form onSubmit={handleSendCode} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                  <div className="relative">
                    <Input id="email" type="email" placeholder="Enter your email" value={email} onChange={(e) => setEmail(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 pr-10 bg-background border-border/60 focus:border-primary" />
                    <Mail className="absolute right-3 top-1/2 -translate-y-1/2 size-5 text-muted-foreground" />
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
                <h1 className="text-3xl font-bold tracking-tight mb-2">Enter code</h1>
                <p className="text-muted-foreground text-sm">We sent a 6-digit code to <strong>{email}</strong></p>
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
                <h1 className="text-3xl font-bold tracking-tight mb-2">New password</h1>
                <p className="text-muted-foreground text-sm">Create a new password for your account</p>
              </div>
              <form onSubmit={handleResetPassword} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="newPassword" className="text-sm font-medium">New Password</Label>
                  <div className="relative">
                    <Input id="newPassword" type={showPassword ? "text" : "password"} placeholder="Enter new password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required minLength={8} className="h-12 pr-10 bg-background border-border/60 focus:border-primary" />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                      {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirm Password</Label>
                  <div className="relative">
                    <Input id="confirmPassword" type={showConfirmPassword ? "text" : "password"} placeholder="Confirm new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} onFocus={() => setIsTyping(true)} onBlur={() => setIsTyping(false)} required className="h-12 pr-10 bg-background border-border/60 focus:border-primary" />
                    <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
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
              <h1 className="text-2xl font-bold tracking-tight mb-3">Password reset!</h1>
              <p className="text-muted-foreground text-sm mb-6">Your password has been updated. You can now log in with your new password.</p>
              <Button className="w-full h-12" onClick={() => router.push('/login')}>
                <Lock className="mr-2 size-4" />Go to login
              </Button>
            </div>
          )}

          {step !== 'success' && (
            <div className="text-center text-sm text-muted-foreground mt-8">
              Remember your password? <Link href="/login" className="text-foreground font-medium hover:underline">Sign in</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
