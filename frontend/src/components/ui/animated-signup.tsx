"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, Sparkles } from "lucide-react";
import { auth } from "@/lib/api";

// Floating geometric shapes that follow mouse
interface FloatingShapeProps {
  size: number;
  color: string;
  delay: number;
  mouseX: number;
  mouseY: number;
  shape: "circle" | "square" | "triangle";
}

const FloatingShape = ({ size, color, delay, mouseX, mouseY, shape }: FloatingShapeProps) => {
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  
  useEffect(() => {
    const timer = setTimeout(() => {
      const moveX = (mouseX - window.innerWidth / 2) * 0.02 * (size / 100);
      const moveY = (mouseY - window.innerHeight / 2) * 0.02 * (size / 100);
      setOffset({ x: moveX, y: moveY });
    }, delay);
    return () => clearTimeout(timer);
  }, [mouseX, mouseY, delay, size]);

  const baseStyle = {
    width: size,
    height: size,
    backgroundColor: color,
    transform: `translate(${offset.x}px, ${offset.y}px)`,
    transition: 'transform 0.3s ease-out',
  };

  if (shape === "circle") {
    return <div className="rounded-full absolute" style={{ ...baseStyle, borderRadius: '50%' }} />;
  } else if (shape === "square") {
    return <div className="absolute" style={{ ...baseStyle, borderRadius: size * 0.2 }} />;
  } else {
    // Triangle using clip-path
    return (
      <div 
        className="absolute" 
        style={{ 
          width: 0, 
          height: 0, 
          borderLeft: `${size/2}px solid transparent`,
          borderRight: `${size/2}px solid transparent`,
          borderBottom: `${size}px solid ${color}`,
          transform: `translate(${offset.x}px, ${offset.y}px)`,
          transition: 'transform 0.3s ease-out',
        }} 
      />
    );
  }
};

// Animated growing bars
interface GrowingBarProps {
  height: number;
  delay: number;
  isTyping: boolean;
}

const GrowingBar = ({ height, delay, isTyping }: GrowingBarProps) => {
  const [currentHeight, setCurrentHeight] = useState(height * 0.3);
  
  useEffect(() => {
    if (isTyping) {
      setCurrentHeight(height * 1.2);
    } else {
      const interval = setInterval(() => {
        setCurrentHeight(height * (0.3 + Math.random() * 0.7));
      }, 2000 + delay);
      return () => clearInterval(interval);
    }
  }, [isTyping, height, delay]);

  return (
    <div 
      className="w-8 rounded-t-lg transition-all duration-500 ease-in-out"
      style={{ 
        height: currentHeight,
        backgroundColor: '#6C3FF5',
        transitionDelay: `${delay}ms`,
      }}
    />
  );
};

// Pulsing dots
interface PulsingDotProps {
  size: number;
  delay: number;
  color: string;
}

const PulsingDot = ({ size, delay, color }: PulsingDotProps) => {
  return (
    <div 
      className="rounded-full animate-pulse"
      style={{ 
        width: size, 
        height: size, 
        backgroundColor: color,
        animationDelay: `${delay}ms`,
        animationDuration: '2s',
      }}
    />
  );
};

// Pupil component
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
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;
    return { x, y };
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

// EyeBall component
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
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;
    return { x, y };
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

export default function AnimatedSignupPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const router = useRouter();

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (!agreedToTerms) {
      setError("Please agree to the terms and conditions");
      return;
    }

    setIsLoading(true);

    try {
      await auth.register(username.trim(), email.trim(), password);
      router.push('/chat');
    } catch (err: any) {
      const msg = err.response?.data?.username?.[0] || 
                  err.response?.data?.email?.[0] || 
                  err.response?.data?.password?.[0] || 
                  err.response?.data?.detail || '';
      if (msg.includes('username')) {
        setError('Username already taken. Please choose another.');
      } else if (msg.includes('email')) {
        setError('Email already registered. Please use another or sign in.');
      } else if (msg.includes('password')) {
        setError('Password is too weak. Please use at least 8 characters.');
      } else {
        setError('Registration failed. Please check your information and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Animation Section */}
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-700 p-12 text-white overflow-hidden">
        {/* Floating geometric shapes */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-20">
            <FloatingShape size={80} color="rgba(255,255,255,0.1)" delay={0} mouseX={mouseX} mouseY={mouseY} shape="circle" />
          </div>
          <div className="absolute top-40 right-32">
            <FloatingShape size={60} color="rgba(255,255,255,0.15)" delay={100} mouseX={mouseX} mouseY={mouseY} shape="square" />
          </div>
          <div className="absolute bottom-40 left-40">
            <FloatingShape size={100} color="rgba(255,255,255,0.08)" delay={200} mouseX={mouseX} mouseY={mouseY} shape="triangle" />
          </div>
          <div className="absolute top-60 left-1/3">
            <FloatingShape size={40} color="rgba(255,255,255,0.12)" delay={300} mouseX={mouseX} mouseY={mouseY} shape="circle" />
          </div>
          <div className="absolute bottom-60 right-20">
            <FloatingShape size={70} color="rgba(255,255,255,0.1)" delay={400} mouseX={mouseX} mouseY={mouseY} shape="square" />
          </div>
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

        {/* Center animation - Growing bars with pulsing dots */}
        <div className="relative z-20 flex flex-col items-center justify-center">
          <div className="relative h-[400px] flex items-end justify-center gap-3">
            <GrowingBar height={200} delay={0} isTyping={isTyping} />
            <GrowingBar height={280} delay={100} isTyping={isTyping} />
            <GrowingBar height={160} delay={200} isTyping={isTyping} />
            <GrowingBar height={320} delay={300} isTyping={isTyping} />
            <GrowingBar height={240} delay={400} isTyping={isTyping} />
          </div>
          
          {/* Pulsing dots below bars */}
          <div className="flex gap-4 mt-8">
            <PulsingDot size={12} delay={0} color="rgba(255,255,255,0.6)" />
            <PulsingDot size={16} delay={150} color="rgba(255,255,255,0.5)" />
            <PulsingDot size={10} delay={300} color="rgba(255,255,255,0.7)" />
            <PulsingDot size={14} delay={450} color="rgba(255,255,255,0.6)" />
            <PulsingDot size={12} delay={600} color="rgba(255,255,255,0.5)" />
          </div>

          <div className="mt-12 text-center">
            <h2 className="text-2xl font-bold mb-2">Start Your Journey</h2>
            <p className="text-white/70 text-sm max-w-xs">
              Join thousands of professionals managing their business smarter
            </p>
          </div>
        </div>

        {/* Bottom links */}
        <div className="relative z-20 flex items-center gap-8 text-sm text-white/60">
          <Link href="#" className="hover:text-white transition-colors">
            Privacy Policy
          </Link>
          <Link href="#" className="hover:text-white transition-colors">
            Terms of Service
          </Link>
          <Link href="/login" className="hover:text-white transition-colors">
            Already have an account?
          </Link>
        </div>

        {/* Decorative gradient orbs */}
        <div className="absolute top-1/4 right-1/4 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-white/5 rounded-full blur-3xl" />
      </div>

      {/* Right Signup Section */}
      <div className="flex items-center justify-center p-8 bg-background overflow-y-auto">
        <div className="w-full max-w-[420px] py-8">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-8">
            <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="size-4 text-primary" />
            </div>
            <span>AEIOU AI</span>
          </div>

          {/* Header */}
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold tracking-tight mb-2">Create your account</h1>
            <p className="text-muted-foreground text-sm">Please enter your details</p>
          </div>

          {/* Signup Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Choose a username"
                value={username}
                autoComplete="off"
                onChange={(e) => setUsername(e.target.value)}
                onFocus={() => setIsTyping(true)}
                onBlur={() => setIsTyping(false)}
                required
                className="h-11 bg-background border-border/60 focus:border-primary"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                autoComplete="off"
                onChange={(e) => setEmail(e.target.value)}
                onFocus={() => setIsTyping(true)}
                onBlur={() => setIsTyping(false)}
                required
                className="h-11 bg-background border-border/60 focus:border-primary"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a strong password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                  required
                  className="h-11 pr-10 bg-background border-border/60 focus:border-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirm Password</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  onFocus={() => setIsTyping(true)}
                  onBlur={() => setIsTyping(false)}
                  required
                  className="h-11 pr-10 bg-background border-border/60 focus:border-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-start space-x-2 pt-2">
              <Checkbox 
                id="terms" 
                checked={agreedToTerms}
                onCheckedChange={(checked) => setAgreedToTerms(checked as boolean)}
              />
              <Label
                htmlFor="terms"
                className="text-sm font-normal cursor-pointer leading-tight"
              >
                I agree to the{' '}
                <Link href="#" className="text-primary hover:underline">
                  Terms of Service
                </Link>{' '}
                and{' '}
                <Link href="#" className="text-primary hover:underline">
                  Privacy Policy
                </Link>
              </Label>
            </div>

            {error && (
              <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">
                {error}
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full h-12 text-base font-medium" 
              size="lg" 
              disabled={isLoading}
            >
              {isLoading ? "Creating account..." : "Sign Up"}
            </Button>
          </form>

          {/* Login Link */}
          <div className="text-center text-sm text-muted-foreground mt-8">
            Already have an account?{" "}
            <a href="/login" className="text-foreground font-medium hover:underline">
              Log in
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
