"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckSquare, FileText, MessageSquare, TrendingUp } from "lucide-react";

const HeroSection = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section className="relative w-full overflow-hidden bg-slate-50 min-h-[92vh] flex items-center justify-center">
      {/* Grid background */}
      <div className="absolute inset-0 z-0 pointer-events-none grid-dna" />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center text-center px-6 w-full max-w-6xl mx-auto pt-24 pb-10">
        {/* Pill badge */}
        <div
          className={`inline-flex items-center gap-2 h-9 px-4 rounded-full bg-white border border-slate-200/80 shadow-sm transition-all duration-700 ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"
          }`}
        >
          <span className="bg-indigo-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider">
            New
          </span>
          <span className="text-sm font-medium text-slate-600">
            AI business command center for tasks, docs, and decisions
          </span>
        </div>

        {/* Headline — "Magic UI" typographic feel */}
        <h1
          className={`mt-8 transition-all duration-700 delay-100 ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          <span className="block text-5xl sm:text-6xl lg:text-[78px] font-extrabold leading-[1.05] text-slate-900">
            AEIOU AI
          </span>
          <span className="block text-4xl sm:text-5xl lg:text-[64px] font-extrabold leading-[1.08] mt-2 text-slate-900">
            Run work from one business brain
          </span>
        </h1>

        {/* Subtitle */}
        <p
          className={`mt-7 text-lg md:text-xl text-slate-500 max-w-[600px] leading-relaxed font-medium transition-all duration-700 delay-200 ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          Upload business documents, chat with Aiden, turn conversations into tasks,
          and keep decisions tied to the context your company already has.
        </p>

        {/* CTA Buttons */}
        <div
          className={`flex flex-col sm:flex-row items-center gap-3 mt-10 transition-all duration-700 delay-300 ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          <Link href="/register">
            <button className="group relative px-7 py-3 rounded-lg bg-indigo-600 text-white font-medium text-[15px] hover:bg-slate-900 transition-all duration-300 shadow-sm overflow-hidden">
              <span className="relative z-10 flex items-center gap-2">
                Start your command center
              </span>
            </button>
          </Link>
          <Link href="/features">
            <button className="px-8 py-3.5 rounded-xl bg-white text-slate-700 border border-slate-200 font-semibold text-[15px] hover:border-slate-300 hover:shadow-md transition-all duration-300">
              See workflows
            </button>
          </Link>
        </div>

        {/* Product proof */}
        <div
          className={`mt-14 w-full max-w-4xl transition-all duration-700 delay-[400ms] ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-left">
            {[
              { title: "Ask Aiden", body: "Get answers grounded in your workspace.", icon: MessageSquare },
              { title: "Upload docs", body: "Extract decisions from files and notes.", icon: FileText },
              { title: "Create tasks", body: "Move from chat to tracked outcomes.", icon: CheckSquare },
              { title: "See status", body: "Review fast, cached business signals.", icon: TrendingUp },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
                  <Icon className="w-4 h-4 text-indigo-600 mb-3" />
                  <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{item.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

export { HeroSection };
