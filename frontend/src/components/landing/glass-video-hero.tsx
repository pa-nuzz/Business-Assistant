"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { CpuArchitecture } from "@/components/landing/cpu-architecture";

const trustLetters = ["A", "E", "I", "O", "U"];
const trustColors = [
  "from-violet-500 to-indigo-600 text-white border-violet-200",
  "from-sky-400 to-cyan-500 text-white border-sky-200",
  "from-amber-300 to-yellow-400 text-slate-900 border-amber-200",
  "from-emerald-400 to-teal-500 text-white border-emerald-200",
  "from-rose-400 to-pink-500 text-white border-rose-200",
];

const HeroSection = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section className="relative overflow-hidden bg-slate-50">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 grid-dna" />
        <div className="absolute left-1/2 top-0 h-[320px] w-[560px] -translate-x-1/2 rounded-full bg-indigo-400/[0.09] blur-[120px]" />
        <div className="absolute left-[12%] top-[28%] h-40 w-40 rounded-full bg-violet-300/10 blur-3xl" />
        <div className="absolute right-[12%] top-[20%] h-48 w-48 rounded-full bg-cyan-300/10 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto grid min-h-[92vh] w-full max-w-[1200px] items-center gap-14 px-8 pb-20 pt-32 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="flex flex-col items-center text-center lg:items-start lg:text-left">
          <div
            className={`text-[12px] font-semibold uppercase tracking-[0.16em] text-slate-400 transition-all duration-700 ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0"
            }`}
          >
            AEIOU AI
          </div>

          <h1
            className={`mt-5 transition-all duration-700 delay-100 ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
            }`}
          >
            <span className="block text-4xl font-extrabold leading-[1.02] tracking-[-0.055em] text-slate-900 sm:text-6xl lg:text-[76px]">
              Run work from one{" "}
              <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
                business brain
              </span>
            </span>
          </h1>

          <div
            className={`mt-8 flex flex-col items-center gap-4 transition-all duration-700 delay-300 sm:flex-row lg:items-center ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
            }`}
          >
            <Link href="/register">
              <button className="h-11 rounded-full bg-indigo-600 px-6 text-[14px] font-semibold text-white shadow-[0_10px_24px_rgba(79,70,229,0.16)] transition-all duration-200 hover:bg-slate-900 hover:shadow-[0_14px_28px_rgba(15,23,42,0.14)]">
                <span className="relative z-10 flex items-center gap-2">
                  Start your command center
                </span>
              </button>
            </Link>
            <Link href="/features">
              <button className="group flex h-11 items-center gap-2 px-1 text-[14px] font-semibold text-slate-600 transition-colors duration-200 hover:text-slate-900">
                See workflows
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </button>
            </Link>
          </div>

          <div
            className={`mt-14 flex flex-col items-center gap-2 transition-all duration-700 delay-[400ms] lg:items-start ${
              mounted ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="flex -space-x-1.5">
                <span className="h-4 w-4 rounded-full border border-slate-200 bg-white/95" />
                <span className="h-4 w-4 rounded-full border border-slate-200 bg-white/95" />
                <span className="h-4 w-4 rounded-full border border-slate-200 bg-white/95" />
              </div>
              <div className="flex items-center -space-x-2">
                {trustLetters.map((letter, index) => (
                  <span
                    key={letter}
                    className={`flex h-7 w-7 items-center justify-center rounded-full border bg-gradient-to-br text-[10px] font-extrabold shadow-[0_8px_18px_rgba(15,23,42,0.12)] ${trustColors[index]}`}
                  >
                    {letter}
                  </span>
                ))}
              </div>
            </div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
              Trusted by many more
            </p>
          </div>
        </div>

        <div
          className={`relative mx-auto w-full max-w-[560px] transition-all duration-700 delay-200 ${
            mounted ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"
          }`}
        >
          <div className="absolute inset-x-[-8%] top-1/2 h-[86%] -translate-y-1/2 bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.96)_0%,rgba(255,255,255,0.72)_42%,rgba(255,255,255,0)_72%)] blur-sm" />
          <div className="absolute inset-x-6 top-1/2 h-24 -translate-y-1/2 bg-indigo-300/10 blur-3xl" />
          <div className="absolute inset-x-[8%] top-1/2 h-px -translate-y-1/2 bg-gradient-to-r from-transparent via-white to-transparent" />
          <CpuArchitecture
            className="relative mx-auto aspect-[2/1] w-full text-slate-500"
            text="AEIOU"
            lineMarkerSize={14}
          />
        </div>
      </div>
    </section>
  );
};

export { HeroSection };
