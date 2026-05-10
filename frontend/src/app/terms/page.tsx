'use client';

import { Footer } from "@/components/landing/footer";
import { motion } from "framer-motion";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden">
      {/* Exact Original Linear Grid Design */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 grid-dna"></div>
      </div>

      <section className="pt-40 pb-20 relative z-10">
        <div className="container mx-auto px-6 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-16"
          >
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-slate-900 mb-4">Terms of Service</h1>
            <p className="text-slate-500 font-bold uppercase tracking-widest text-xs">Last Updated: May 9, 2026</p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="p-10 md:p-16 rounded-[40px] bg-white border border-slate-200 shadow-[0_4px_20px_rgb(0,0,0,0.02)] prose prose-slate max-w-none"
          >
            <h2 className="text-2xl font-bold text-slate-900 mb-6">1. Acceptance of Terms</h2>
            <p className="text-slate-600 leading-relaxed mb-10 font-medium">
              By accessing or using AEIOU AI, you agree to be bound by these Terms of Service. If you do not agree to all of these terms, do not use the service.
            </p>

            <h2 className="text-2xl font-bold text-slate-900 mb-6">2. Description of Service</h2>
            <p className="text-slate-600 leading-relaxed mb-10 font-medium">
              AEIOU AI provides an AI-powered business workspace including chat, document analysis, and task management. We reserve the right to modify or discontinue the service at any time.
            </p>

            <h2 className="text-2xl font-bold text-slate-900 mb-6">3. User Responsibilities</h2>
            <p className="text-slate-600 leading-relaxed font-medium">
              You are responsible for maintaining the confidentiality of your account and for all activities that occur under your account. You agree to use the service only for lawful purposes.
            </p>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
