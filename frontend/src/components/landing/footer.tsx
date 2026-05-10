'use client';

import { useState } from "react";
import Link from "next/link";
import { AnimatedLogo } from "@/components/ui/animated-logo";
import { Send, ArrowUpRight, GitBranch, Users, Mail } from "lucide-react";
import { toast } from "sonner";

type FooterLink = { label: string; href: string; external?: boolean };

const footerLinks: Record<string, FooterLink[]> = {
  Platform: [
    { label: "Features", href: "/features" },
    { label: "Pricing", href: "/pricing" },
    { label: "About", href: "/about" },
  ],
  Connect: [
    { label: "Support", href: "/contact" },
    { label: "LinkedIn", href: "https://www.linkedin.com/in/anuzpaudel/", external: true },
    { label: "GitHub", href: "https://github.com/pa-nuzz", external: true },
  ],
  Legal: [
    { label: "Privacy Policy", href: "/privacy" },
    { label: "Terms of Service", href: "/terms" },
    { label: "Contact", href: "mailto:anuj.paudel061@gmail.com", external: true },
  ],
};

export function Footer() {
  const [email, setEmail] = useState("");

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    toast.success("Thanks for subscribing! We'll keep you updated.");
    setEmail("");
  };

  return (
    <footer className="relative bg-slate-900 text-slate-300 overflow-hidden">
      {/* Top gradient line */}
      <div className="h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />

      {/* Subtle grid */}
      <div className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage: "linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />

      {/* Ambient */}
      <div className="absolute top-0 left-1/3 w-[400px] h-[200px] bg-indigo-500/[0.04] blur-[100px] pointer-events-none" />

      <div className="container mx-auto px-6 relative z-10">
        {/* Newsletter strip */}
        <div className="py-10 border-b border-white/[0.06] flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-white font-bold text-lg tracking-tight">Stay in the loop</h3>
            <p className="text-sm text-slate-400 mt-1">Get product updates and insights. No spam.</p>
          </div>
          <form onSubmit={handleSubscribe} className="flex w-full md:w-auto">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Your email"
              required
              className="h-11 px-4 bg-white/[0.06] border border-white/[0.08] rounded-l-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/50 focus:bg-white/[0.08] transition-all w-full md:w-64"
            />
            <button
              type="submit"
              className="h-11 px-5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-r-xl text-sm font-semibold flex items-center gap-2 transition-colors shrink-0"
            >
              <Send className="w-3.5 h-3.5" />
              Subscribe
            </button>
          </form>
        </div>

        {/* Main grid */}
        <div className="py-12 grid grid-cols-2 md:grid-cols-12 gap-10 md:gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-4">
            <Link href="/" className="flex items-center gap-2.5 group mb-5">
              <div className="w-8 h-8 rounded-lg bg-white/[0.08] border border-white/[0.06] flex items-center justify-center group-hover:bg-indigo-600/20 transition-colors">
                <AnimatedLogo className="w-5 h-5 brightness-200" />
              </div>
              <span className="text-lg font-bold text-white tracking-tight">AEIOU AI</span>
            </Link>
            <p className="text-sm text-slate-400 leading-relaxed max-w-xs">
              The most intelligent workspace for modern teams. Unified, context-aware, and fast.
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title} className="col-span-1 md:col-span-2 md:col-start-auto">
              <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.15em] mb-5">
                {title}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    {link.external ? (
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-slate-400 hover:text-white transition-colors inline-flex items-center gap-1 group/link"
                      >
                        {link.label}
                        <ArrowUpRight className="w-3 h-3 opacity-0 -translate-y-0.5 translate-x-0.5 group-hover/link:opacity-100 group-hover/link:translate-y-0 group-hover/link:translate-x-0 transition-all" />
                      </a>
                    ) : (
                      <Link
                        href={link.href}
                        className="text-sm text-slate-400 hover:text-white transition-colors"
                      >
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="py-6 border-t border-white/[0.06] flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-500">
            &copy; {new Date().getFullYear()} AEIOU AI. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <a href="https://github.com/pa-nuzz" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-white transition-colors">
              <GitBranch className="w-4 h-4" />
            </a>
            <a href="https://www.linkedin.com/in/anuzpaudel/" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-white transition-colors">
              <Users className="w-4 h-4" />
            </a>
            <a href="mailto:anuj.paudel061@gmail.com" className="text-slate-500 hover:text-white transition-colors">
              <Mail className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
