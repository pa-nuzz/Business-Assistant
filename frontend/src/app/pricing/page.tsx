'use client';

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/landing/footer";
import { Check, Zap } from "lucide-react";
import { motion } from "framer-motion";

const tiers = [
  {
    name: "Starter",
    price: "$0",
    period: "/mo",
    description: "For individuals exploring AI-powered productivity.",
    features: ["AI chat with Gemini", "3 documents/month", "Basic task board", "Community support"],
    cta: "Get Started Free",
    href: "/register",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/mo",
    description: "For professionals who need AI that understands their business.",
    features: ["All AI providers", "Unlimited documents", "Advanced Kanban", "Priority support", "Goal tracking", "Real-time collaboration"],
    cta: "Start Pro Trial",
    href: "/register",
    highlight: true,
  },
  {
    name: "Team",
    price: "$99",
    period: "/mo",
    description: "For teams building together with shared AI context.",
    features: ["Everything in Pro", "Team workspaces", "Shared AI memory", "Admin controls", "SSO (coming soon)", "Dedicated onboarding"],
    cta: "Contact Sales",
    href: "/contact",
    highlight: false,
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden">
      {/* Exact Original Linear Grid Design */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 grid-dna"></div>
        <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-indigo-500 opacity-20 blur-[100px]"></div>
      </div>

      <section className="pt-32 pb-20 relative z-10">
        <div className="container mx-auto px-6 text-center">
          <motion.h1 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900 mb-4"
          >
            Simple, transparent pricing
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-lg text-slate-600 max-w-xl mx-auto mb-14"
          >
            Start free. Upgrade when AI becomes indispensable to your workflow.
          </motion.p>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {tiers.map((tier, i) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`relative rounded-3xl border p-8 text-left card-hover ${
                  tier.highlight
                    ? "border-indigo-600 bg-indigo-50/30 shadow-lg"
                    : "border-slate-200 bg-white"
                }`}
              >
                {tier.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest">
                    Most Popular
                  </div>
                )}
                <h3 className="text-lg font-bold text-slate-900 mb-1">{tier.name}</h3>
                <div className="flex items-baseline gap-1 mb-3">
                  <span className="text-3xl font-bold text-slate-900">{tier.price}</span>
                  <span className="text-slate-500 text-sm">{tier.period}</span>
                </div>
                <p className="text-sm text-slate-500 mb-6 leading-relaxed">{tier.description}</p>
                <ul className="space-y-3 mb-8">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm font-medium text-slate-700">
                      <Check className="w-4 h-4 text-indigo-600 mt-0.5 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link href={tier.href} className="block">
                  <Button variant={tier.highlight ? "default" : "outline"} className={`w-full h-12 rounded-xl font-bold ${tier.highlight ? 'bg-indigo-600 hover:bg-indigo-700 text-white border-none' : ''}`}>
                    {tier.cta}
                  </Button>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
