"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Building2, Sparkles } from "lucide-react";
import api from "@/lib/api";

interface OnboardingStatus {
  has_business_profile: boolean;
  has_conversations: boolean;
  has_documents: boolean;
  has_tasks: boolean;
  completion_pct: number;
  steps_completed: string[];
  total_steps: number;
}

interface OnboardingWizardProps {
  onClose: () => void;
}

export function OnboardingWizard({ onClose }: OnboardingWizardProps) {
  const [step, setStep] = useState(1);
  const [isVisible, setIsVisible] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [, setShowCopied] = useState(false);

  // Check onboarding status on mount
  useEffect(() => {
    const checkStatus = async () => {
      const dismissed = localStorage.getItem("onboarding_dismissed") === "true";
      if (dismissed) return;

      try {
        const response = await api.get("/onboarding/status/");
        const status: OnboardingStatus = response.data;
        
        if (status.completion_pct < 100) {
          setIsVisible(true);
        }
      } catch {
        // Silently fail - don't show wizard if API fails
      }
    };

    checkStatus();
  }, []);

  const handleSkip = () => {
    localStorage.setItem("onboarding_dismissed", "true");
    setIsVisible(false);
    onClose();
  };

  const handleComplete = () => {
    localStorage.setItem("onboarding_dismissed", "true");
    setIsVisible(false);
    // Dispatch events to refresh the app
    window.dispatchEvent(new CustomEvent("refresh-conversations"));
    // Refresh onboarding status for badges
    api.get("/onboarding/status/").catch(() => {});
    onClose();
  };

  const saveProfile = async () => {
    if (!companyName.trim()) return;
    
    setIsSubmitting(true);
    try {
      await api.post("/profile/", {
        company_name: companyName,
        industry: industry || undefined,
      });
      setStep(3);
    } catch {
      // Continue anyway
      setStep(3);
    } finally {
      setIsSubmitting(false);
    }
  };

  const seedDemoData = async () => {
    setIsSubmitting(true);
    try {
      await api.post("/demo/seed/");
    } catch {
      // Continue anyway
    } finally {
      setIsSubmitting(false);
      setStep(4);
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText("");
      setShowCopied(true);
      setTimeout(() => setShowCopied(false), 1500);
    } catch {
      // Ignore copy errors
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-8"
      >
        {/* Progress bar */}
        <div className="flex items-center justify-center mb-8">
          {[1, 2, 3, 4].map((s, idx) => (
            <React.Fragment key={s}>
              <div
                className={`w-3 h-3 rounded-full transition-colors ${
                  step >= s ? "bg-blue-600" : "bg-gray-200"
                }`}
              />
              {idx < 3 && (
                <div
                  className={`w-12 h-0.5 transition-colors ${
                    step > s ? "bg-blue-600" : "bg-gray-200"
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="text-center"
            >
              <div className="w-16 h-16 mx-auto mb-6 relative">
                <img 
                  src="/logos/app-logo.svg" 
                  alt="AEIOU AI" 
                  className="w-full h-full object-contain"
                />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Welcome to AEIOU AI
              </h2>
              <p className="text-gray-600 mb-8">
                Your AI-powered business command center. Let&apos;s get you set up in 2 minutes.
              </p>
              <button
                onClick={() => setStep(2)}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors"
              >
                Get started &rarr;
              </button>
              <button
                onClick={handleSkip}
                className="mt-4 text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Skip for now
              </button>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <div className="flex items-center justify-center mb-6">
                <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-blue-600" />
                </div>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">
                Tell us about your business
              </h2>
              <p className="text-gray-600 text-center mb-6">
                This helps AEIOU give you relevant insights
              </p>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company name *
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Enter your company name"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Industry
                  </label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 bg-white"
                  >
                    <option value="">Select an industry</option>
                    <option value="Technology">Technology</option>
                    <option value="Finance">Finance</option>
                    <option value="Healthcare">Healthcare</option>
                    <option value="Retail">Retail</option>
                    <option value="Consulting">Consulting</option>
                    <option value="E-commerce">E-commerce</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <button
                onClick={saveProfile}
                disabled={!companyName.trim() || isSubmitting}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium rounded-xl transition-colors"
              >
                {isSubmitting ? "Saving..." : "Save & continue &rarr;"}
              </button>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="text-center"
            >
              <div className="flex items-center justify-center mb-6">
                <div className="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-purple-600" />
                </div>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                We&apos;ve loaded sample data
              </h2>
              <p className="text-gray-600 mb-8">
                Explore AEIOU with pre-loaded conversations, tasks, and examples — or jump straight in with your own data.
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(4)}
                  className="flex-1 py-3 px-4 border border-gray-300 hover:border-gray-400 text-gray-700 font-medium rounded-xl transition-colors"
                >
                  Start fresh
                </button>
                <button
                  onClick={seedDemoData}
                  disabled={isSubmitting}
                  className="flex-1 py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium rounded-xl transition-colors"
                >
                  {isSubmitting ? "Loading..." : "Explore demo data &rarr;"}
                </button>
              </div>
            </motion.div>
          )}

          {step === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="text-center"
            >
              <div className="flex items-center justify-center mb-6">
                <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    className="w-10 h-10 text-green-600"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                    />
                    <motion.path
                      d="M8 12l3 3 5-6"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{ duration: 0.6, delay: 0.2 }}
                    />
                  </svg>
                </div>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                You&apos;re all set!
              </h2>
              <p className="text-gray-600 mb-8">
                AEIOU AI is ready. Ask anything about your business.
              </p>

              <button
                onClick={handleComplete}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors"
              >
                Start chatting &rarr;
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
