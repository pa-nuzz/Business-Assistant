"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles, Zap, Shield, BarChart } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.5,
      ease: [0.16, 1, 0.3, 1] as const,
    },
  },
};

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-background via-muted/50 to-primary/5">
      {/* Background decorations */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-400/10 rounded-full blur-3xl" />
      </div>

      <motion.div
        className="container mx-auto px-6 py-20 relative z-10"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <div className="max-w-4xl mx-auto text-center">
          {/* Logo */}
          <motion.div variants={itemVariants} className="flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center overflow-hidden bg-gradient-to-br from-primary to-primary/80 shadow-lg">
              <img src="/logos/app-logo.svg" alt="AEIOU AI" className="w-full h-full object-contain p-2" />
            </div>
            <span className="text-2xl font-bold text-foreground">AEIOU AI</span>
          </motion.div>

          {/* Badge */}
          <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">Your AI Business Partner</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={itemVariants}
            className="text-5xl md:text-7xl font-bold tracking-tight text-foreground mb-6"
          >
            Manage Your Business
            <br />
            <span className="text-primary">With AI Intelligence</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            variants={itemVariants}
            className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed"
          >
            Chat with AI, track tasks, analyze documents, and stay organized — all in one intelligent workspace designed for modern businesses.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/register">
              <Button size="lg" className="h-14 px-8 text-base font-medium shadow-lg">
                Get Started Free
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="h-14 px-8 text-base font-medium border-primary/30 text-primary hover:bg-primary/5">
                Sign In
              </Button>
            </Link>
          </motion.div>

          {/* Trust indicators */}
          <motion.div variants={itemVariants} className="mt-16 flex flex-wrap items-center justify-center gap-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-emerald-500" />
              <span>Lightning Fast</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              <span>Secure & Private</span>
            </div>
            <div className="flex items-center gap-2">
              <BarChart className="w-5 h-5 text-primary" />
              <span>Smart Analytics</span>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
}
