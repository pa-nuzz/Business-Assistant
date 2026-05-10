'use client';

import { useState } from "react";
import { Footer } from "@/components/landing/footer";
import { motion } from "framer-motion";
import { Clock, MapPin } from "lucide-react";
import Image from "next/image";
import { toast } from "sonner";

export default function ContactPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      toast.success("Message sent! We'll get back to you shortly.");
      setIsSubmitting(false);
      (e.target as HTMLFormElement).reset();
    }, 1200);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 grid-dna" />
        <div className="absolute left-1/2 top-0 -translate-x-1/2 w-[500px] h-[300px] rounded-full bg-indigo-400/[0.07] blur-[100px]" />
      </div>

      <section className="flex-1 pt-36 pb-24 relative z-10 flex flex-col justify-center">
        <div className="container mx-auto px-10 max-w-[1200px]">
          {/* Header */}
          <div className="max-w-2xl mb-14">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-slate-200/80 shadow-sm text-sm font-medium text-slate-600 mb-6"
            >
              <div className="relative flex items-center justify-center">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <div className="absolute w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-75" />
              </div>
              Active &amp; Responding
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="text-4xl md:text-6xl font-extrabold tracking-[-0.03em] text-slate-900 mb-4"
            >
              Get in{" "}
              <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
                touch
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="text-lg text-slate-500 leading-relaxed"
            >
              Have a question, idea, or partnership in mind? We&rsquo;d love to hear from you.
            </motion.p>
          </div>

          <div className="grid lg:grid-cols-5 gap-10">
            {/* Left Column — Contact Info */}
            <div className="lg:col-span-2 space-y-5">
              {/* Swag Founder Card */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="group relative p-8 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition-all duration-300 text-center overflow-hidden"
              >
                {/* Subtle top glow */}
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 w-40 h-40 bg-indigo-500/10 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-all duration-700 pointer-events-none" />

                <div className="flex justify-center mb-6 relative z-10">
                  <div className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-[2rem] bg-slate-100 border-4 border-white shadow-[0_8px_20px_rgba(0,0,0,0.08)] overflow-hidden group-hover:scale-105 group-hover:shadow-[0_12px_24px_rgba(99,102,241,0.25)] transition-all duration-500">
                    <Image 
                      src="/founder.jpg" 
                      alt="Anuj Paudel" 
                      fill
                      className="object-cover object-top grayscale opacity-90 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-500" 
                    />
                  </div>
                </div>

                <div className="relative z-10 mb-6">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <div className="text-xl font-extrabold text-slate-900 tracking-tight">Anuj Paudel</div>
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse ring-2 ring-emerald-500/20" title="Online" />
                  </div>
                  <div className="text-sm font-medium text-indigo-600">Founder &amp; Developer</div>
                </div>

                <div className="space-y-2 relative z-10">
                  <a
                    href="https://github.com/pa-nuzz"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between p-3.5 rounded-lg bg-slate-50 border border-slate-100 hover:border-slate-200 transition-all duration-200"
                  >
                    <span className="text-[13px] font-semibold text-slate-700">GitHub</span>
                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Code</span>
                  </a>
                  <a
                    href="https://www.linkedin.com/in/anuzpaudel/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between p-3.5 rounded-lg bg-slate-50 border border-slate-100 hover:border-slate-200 transition-all duration-200"
                  >
                    <span className="text-[13px] font-semibold text-slate-700">LinkedIn</span>
                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Connect</span>
                  </a>
                </div>
              </motion.div>

              {/* Info Cards Grid */}
              <div className="grid grid-cols-2 gap-3">
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 }}
                  className="p-5 rounded-xl bg-white border border-slate-200/80 shadow-sm"
                >
                  <Clock className="w-4 h-4 text-indigo-500 mb-3" />
                  <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Response
                  </div>
                  <div className="text-sm font-bold text-slate-900">&lt; 12 Hours</div>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="p-5 rounded-xl bg-white border border-slate-200/80 shadow-sm"
                >
                  <MapPin className="w-4 h-4 text-indigo-500 mb-3" />
                  <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Timezone
                  </div>
                  <div className="text-sm font-bold text-slate-900">UTC+5:45</div>
                </motion.div>
              </div>
            </div>

            {/* Right Column — Form */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.12 }}
              className="lg:col-span-3 p-8 md:p-10 rounded-xl bg-white border border-slate-200/80 shadow-sm"
            >
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-5">
                  <div className="space-y-2">
                    <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Name
                    </label>
                    <input
                      type="text"
                      required
                      className="w-full h-11 bg-white border border-slate-200 rounded-lg px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors text-sm font-medium text-slate-900 placeholder:text-slate-400"
                      placeholder="Your full name"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Email
                    </label>
                    <input
                      type="email"
                      required
                      className="w-full h-11 bg-white border border-slate-200 rounded-lg px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors text-sm font-medium text-slate-900 placeholder:text-slate-400"
                      placeholder="you@example.com"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Message
                  </label>
                  <textarea
                    required
                    rows={5}
                    className="w-full bg-white border border-slate-200 rounded-lg p-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors text-sm font-medium text-slate-900 placeholder:text-slate-400 resize-none leading-relaxed"
                    placeholder="Tell us about your project or question..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-11 py-0 bg-indigo-600 hover:bg-slate-900 text-white font-medium text-[14px] rounded-lg shadow-sm transition-colors duration-200 flex items-center justify-center disabled:opacity-60"
                >
                  {isSubmitting ? "Sending..." : "Send Message"}
                </button>
              </form>
            </motion.div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
