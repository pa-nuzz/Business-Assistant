"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { AnimatedLogo } from "@/components/ui/animated-logo";

const NAV_ITEMS = [
  { label: "Features", href: "/features" },
  { label: "Pricing", href: "/pricing" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
];

export function Navigation() {
  const router = useRouter();
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex justify-center px-4 pt-4 sm:pt-6 transition-all duration-500 pointer-events-none">
      <nav className={cn(
        "w-full max-w-[1200px] transition-all duration-500 rounded-[24px] pointer-events-auto relative",
        isScrolled 
          ? "bg-white/95 backdrop-blur-xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] py-2.5 px-2 border border-slate-200/60" 
          : "bg-white/80 backdrop-blur-lg border border-transparent py-4 px-2 shadow-[0_4px_24px_rgba(0,0,0,0.04)]"
      )}>
        <div className="flex items-center justify-between px-4 sm:px-6 relative z-10">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 shrink-0 group">
            <div className="w-10 h-10 rounded-2xl bg-white border border-slate-100 flex items-center justify-center transition-transform duration-300 group-hover:scale-105 shadow-sm">
              <AnimatedLogo className="w-6 h-6" />
            </div>
            <span className="text-xl font-bold text-slate-900 tracking-tight">
              AEIOU AI
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1 absolute left-1/2 -translate-x-1/2">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "px-4 py-2 rounded-full text-[14px] font-semibold transition-all duration-300",
                  pathname === item.href
                    ? "text-slate-900 bg-slate-100/50"
                    : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                )}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* CTA */}
          <div className="hidden md:flex items-center gap-2">
            <Link href="/login">
              <Button variant="ghost" className="text-slate-500 hover:text-slate-900 font-semibold rounded-full px-5 h-11 text-[14px] transition-colors">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-indigo-600 hover:bg-slate-900 text-white shadow-sm rounded-full px-6 h-11 transition-colors font-semibold text-[14px]">
                Get Started
              </Button>
            </Link>
          </div>

          {/* Mobile Toggle */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden w-10 h-10 flex items-center justify-center rounded-xl transition-colors text-slate-600 hover:bg-slate-100"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden absolute top-full left-0 right-0 mt-2 p-4 bg-white/95 backdrop-blur-xl border border-slate-200/60 shadow-xl rounded-3xl animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="flex flex-col gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center py-3 px-4 rounded-xl font-semibold text-[15px] transition-colors",
                    pathname === item.href
                      ? "bg-slate-50 text-slate-900"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  )}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </div>
            <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-slate-100">
              <Link href="/login" onClick={() => setIsMobileMenuOpen(false)}>
                <Button variant="ghost" className="w-full justify-center text-slate-600 font-semibold h-12 rounded-xl">
                  Sign In
                </Button>
              </Link>
              <Link href="/register" onClick={() => setIsMobileMenuOpen(false)}>
                <Button className="w-full bg-indigo-600 text-white font-semibold h-12 rounded-xl transition-colors hover:bg-slate-900">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        )}
      </nav>
    </div>
  );
}
