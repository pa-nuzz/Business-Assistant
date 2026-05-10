'use client';

import { Footer } from "@/components/landing/footer";
import { motion } from "framer-motion";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden">
      {/* Exact Original Linear Grid Design */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 grid-dna"></div>
        <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-indigo-500 opacity-10 blur-[100px]"></div>
      </div>

      <section className="pt-40 pb-20 relative z-10">
        <div className="container mx-auto px-6 max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100/50 text-[10px] font-bold text-indigo-600 mb-6 uppercase tracking-widest">
              About Us
            </div>
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-slate-900 mb-8">
              Pioneering the next era of <br />
              <span className="text-indigo-600">business intelligence</span>
            </h1>
            <p className="text-xl text-slate-600 font-medium max-w-2xl mx-auto leading-relaxed">
              We build tools that empower teams to turn data into action, conversations into tasks, and goals into reality.
            </p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="p-10 md:p-16 rounded-[40px] bg-white border border-slate-200 shadow-[0_4px_20px_rgb(0,0,0,0.02)] text-left"
          >
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Our Story</h2>
            <p className="text-lg text-slate-600 leading-relaxed font-medium mb-8">
              AEIOU AI was founded with a single goal: to simplify the complex business landscape. By combining advanced AI with intuitive design, we&apos;ve created a workspace that feels like a natural extension of your team.
            </p>
            <p className="text-lg text-slate-600 leading-relaxed font-medium">
              Today, we serve thousands of users who rely on our platform to stay organized, focused, and ahead of the curve.
            </p>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
