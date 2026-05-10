"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/landing/footer";
import { motion } from "framer-motion";

const features = [
  {
    title: "AI-Powered Chat",
    desc: "Context-aware conversations with multi-provider AI and real-time streaming."
  },
  {
    title: "Document Intelligence",
    desc: "Upload PDFs, DOCX, TXT for instant analysis, summarization, and insight extraction."
  },
  {
    title: "Task Management",
    desc: "Visual Kanban board with drag-and-drop and AI-suggested tasks from conversations."
  },
  {
    title: "Goal Tracking",
    desc: "Set business goals and let AI track progress and surface blockers."
  },
  {
    title: "Enterprise Security",
    desc: "JWT auth, httpOnly cookies, rate limiting, and audit logging."
  },
  {
    title: "Real-Time Sync",
    desc: "WebSocket streaming, instant notifications, and live board updates."
  },
];

export default function FeaturesPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 relative overflow-hidden">
      {/* Your Preferred Linear Grid Design */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 grid-dna"></div>
        <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-indigo-500/10 blur-[100px]"></div>
      </div>

      <section className="flex-1 pt-40 pb-20 relative z-10 flex flex-col justify-center">
        <div className="container mx-auto px-10">
          <div className="max-w-3xl mx-auto text-center mb-24">
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-4xl md:text-6xl font-bold tracking-tight text-slate-900 mb-6"
            >
              Everything you need to <br />
              <span className="text-indigo-600">run your business</span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="text-lg text-slate-600 max-w-2xl mx-auto mb-16 leading-relaxed"
            >
              One intelligent workspace replacing chat apps, document tools, and task boards.
            </motion.p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-10 max-w-[1200px] mx-auto text-left">
            {features.map((f, idx) => {
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="group p-8 rounded-xl bg-white border border-slate-200 shadow-[0_4px_20px_rgb(0,0,0,0.02)] hover:shadow-[0_20px_40px_rgb(79,70,229,0.06)] transition-shadow duration-500 relative overflow-hidden flex flex-col h-full"
                >
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-indigo-500 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                  <h3 className="text-xl font-bold text-slate-900 mb-4 tracking-tight">{f.title}</h3>
                  <p className="text-base text-slate-600 leading-relaxed font-medium">{f.desc}</p>
                </motion.div>
              );
            })}
          </div>

          <div className="mt-20 text-center">
            <Link href="/register">
              <Button size="lg" className="h-12 px-10 text-[15px] font-medium rounded-lg bg-indigo-600 hover:bg-slate-900 shadow-sm text-white border-none transition-colors">
                Start Building Today
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
