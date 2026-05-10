'use client';

import { Footer } from "@/components/landing/footer";
import { motion } from "framer-motion";

export default function PrivacyPage() {
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
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-slate-900 mb-4">Privacy Policy</h1>
            <p className="text-slate-500 font-bold uppercase tracking-widest text-xs">Last Updated: May 9, 2026</p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="p-10 md:p-16 rounded-[40px] bg-white border border-slate-200 shadow-[0_4px_20px_rgb(0,0,0,0.02)] prose prose-slate max-w-none"
          >
            <h2 className="text-2xl font-bold text-slate-900 mb-6">1. Data Collection</h2>
            <p className="text-slate-600 leading-relaxed mb-10 font-medium">
              We collect information that you provide directly to us when you create an account, upload documents, or communicate with our AI. This includes your name, email address, and the content of your communications.
            </p>

            <h2 className="text-2xl font-bold text-slate-900 mb-6">2. Use of Information</h2>
            <p className="text-slate-600 leading-relaxed mb-10 font-medium">
              We use the information we collect to provide, maintain, and improve our services, including the AI-powered features of AEIOU. We do not sell your data to third parties.
            </p>

            <h2 className="text-2xl font-bold text-slate-900 mb-6">3. Data Security</h2>
            <p className="text-slate-600 leading-relaxed font-medium">
              We take reasonable measures to help protect information about you from loss, theft, misuse, and unauthorized access. All document uploads are encrypted at rest and in transit.
            </p>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
