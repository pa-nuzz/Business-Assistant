"use client";

import type React from "react";
import { useState, useRef } from "react";
import {
  Search,
  Mic,
  ArrowUp,
  Plus,
  FileText,
  Code,
  BookOpen,
  PenTool,
  BrainCircuit,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function AIAssistantInterface() {
  const [inputValue, setInputValue] = useState("");
  const [searchEnabled, setSearchEnabled] = useState(false);
  const [deepResearchEnabled, setDeepResearchEnabled] = useState(false);
  const [reasonEnabled, setReasonEnabled] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [showUploadAnimation, setShowUploadAnimation] = useState(false);
  const [activeCommandCategory, setActiveCommandCategory] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const commandSuggestions = {
    learn: [
      "Explain business strategy fundamentals",
      "How to optimize cash flow?",
      "What are key marketing metrics?",
      "Explain market segmentation",
      "How to build a sales funnel?",
    ],
    code: [
      "Create a financial projection spreadsheet",
      "Write a Python script for data analysis",
      "How to automate business reports?",
      "Explain API integration for business",
      "Create a dashboard for KPI tracking",
    ],
    write: [
      "Write a professional business proposal",
      "Create a company mission statement",
      "Draft a client outreach email",
      "Write a product launch announcement",
      "Create social media content calendar",
    ],
  };

  const handleUploadFile = () => {
    setShowUploadAnimation(true);
    setTimeout(() => {
      const newFile = `Document.pdf`;
      setUploadedFiles((prev) => [...prev, newFile]);
      setShowUploadAnimation(false);
    }, 1500);
  };

  const handleCommandSelect = (command: string) => {
    setInputValue(command);
    setActiveCommandCategory(null);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleSendMessage = () => {
    if (inputValue.trim()) {
      console.log("Sending message:", inputValue);
      setInputValue("");
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background p-6">
      <div className="w-full max-w-3xl mx-auto flex flex-col items-center">
        {/* Logo with animated gradient */}
        <div className="mb-8 w-20 h-20 relative">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 200 200"
            width="100%"
            height="100%"
            className="w-full h-full"
          >
            <g clipPath="url(#cs_clip_1_ellipse-12)">
              <mask
                id="cs_mask_1_ellipse-12"
                style={{ maskType: "alpha" }}
                width="200"
                height="200"
                x="0"
                y="0"
                maskUnits="userSpaceOnUse"
              >
                <path
                  fill="#fff"
                  fillRule="evenodd"
                  d="M100 150c27.614 0 50-22.386 50-50s-22.386-50-50-50-50 22.386-50 50 22.386 50 50 50zm0 50c55.228 0 100-44.772 100-100S155.228 0 100 0 0 44.772 0 100s44.772 100 100 100z"
                  clipRule="evenodd"
                ></path>
              </mask>
              <g mask="url(#cs_mask_1_ellipse-12)">
                <path fill="#fff" d="M200 0H0v200h200V0z"></path>
                <path fill="#0066FF" fillOpacity="0.33" d="M200 0H0v200h200V0z"></path>
                <g filter="url(#filter0_f_844_2811)" className="animate-gradient">
                  <path fill="#0066FF" d="M110 32H18v68h92V32z"></path>
                  <path fill="#0044FF" d="M188-24H15v98h173v-98z"></path>
                  <path fill="#0099FF" d="M175 70H5v156h170V70z"></path>
                  <path fill="#00CCFF" d="M230 51H100v103h130V51z"></path>
                </g>
              </g>
            </g>
            <defs>
              <filter
                id="filter0_f_844_2811"
                width="385"
                height="410"
                x="-75"
                y="-104"
                colorInterpolationFilters="sRGB"
                filterUnits="userSpaceOnUse"
              >
                <feFlood floodOpacity="0" result="BackgroundImageFix"></feFlood>
                <feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"></feBlend>
                <feGaussianBlur result="effect1_foregroundBlur_844_2811" stdDeviation="40"></feGaussianBlur>
              </filter>
              <clipPath id="cs_clip_1_ellipse-12">
                <path fill="#fff" d="M0 0H200V200H0z"></path>
              </clipPath>
            </defs>
            <g style={{ mixBlendMode: "overlay" }} mask="url(#cs_mask_1_ellipse-12)">
              <path fill="gray" stroke="transparent" d="M200 0H0v200h200V0z" filter="url(#cs_noise_1_ellipse-12)"></path>
            </g>
            <defs>
              <filter id="cs_noise_1_ellipse-12" width="100%" height="100%" x="0%" y="0%" filterUnits="objectBoundingBox">
                <feTurbulence baseFrequency="0.6" numOctaves="5" result="out1" seed="4"></feTurbulence>
                <feComposite in="out1" in2="SourceGraphic" operator="in" result="out2"></feComposite>
                <feBlend in="SourceGraphic" in2="out2" mode="overlay" result="out3"></feBlend>
              </filter>
            </defs>
          </svg>
        </div>

        {/* Welcome message */}
        <div className="mb-10 text-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col items-center"
          >
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-400 mb-2">
              Ready to assist you
            </h1>
            <p className="text-slate-600 max-w-md">
              Ask me anything or try one of the suggestions below
            </p>
          </motion.div>
        </div>

        {/* Input area */}
        <div className="w-full bg-card border border-border rounded-xl shadow-sm overflow-hidden mb-4">
          <div className="p-4">
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask me anything..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="w-full text-slate-900 text-base outline-none placeholder:text-slate-400 bg-transparent"
            />
          </div>

          {/* Uploaded files */}
          {uploadedFiles.length > 0 && (
            <div className="px-4 pb-3">
              <div className="flex flex-wrap gap-2">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 bg-muted py-1 px-2 rounded-md border border-border">
                    <FileText className="w-3 h-3 text-blue-600" />
                    <span className="text-xs text-slate-900">{file}</span>
                    <button onClick={() => removeFile(index)} className="text-slate-400 hover:text-slate-600">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSearchEnabled(!searchEnabled)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  searchEnabled
                    ? "bg-blue-50 text-blue-600 hover:bg-blue-100"
                    : "bg-muted text-slate-600 hover:bg-muted/80"
                }`}
              >
                <Search className="w-4 h-4" />
                <span>Search</span>
              </button>
              <button
                onClick={() => setDeepResearchEnabled(!deepResearchEnabled)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  deepResearchEnabled
                    ? "bg-blue-50 text-blue-600 hover:bg-blue-100"
                    : "bg-muted text-slate-600 hover:bg-muted/80"
                }`}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={deepResearchEnabled ? "text-blue-600" : "text-slate-400"}>
                  <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="2" />
                  <circle cx="8" cy="8" r="3" fill="currentColor" />
                </svg>
                <span>Deep Research</span>
              </button>
              <button
                onClick={() => setReasonEnabled(!reasonEnabled)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  reasonEnabled
                    ? "bg-blue-50 text-blue-600 hover:bg-blue-100"
                    : "bg-muted text-slate-600 hover:bg-muted/80"
                }`}
              >
                <BrainCircuit className={`w-4 h-4 ${reasonEnabled ? "text-blue-600" : "text-slate-400"}`} />
                <span>Reason</span>
              </button>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-2 text-slate-400 hover:text-slate-900 transition-colors">
                <Mic className="w-5 h-5" />
              </button>
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim()}
                className={`w-8 h-8 flex items-center justify-center rounded-full transition-colors ${
                  inputValue.trim()
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : "bg-muted text-slate-600 cursor-not-allowed"
                }`}
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Upload files */}
          <div className="px-4 py-2 border-t border-border">
            <button
              onClick={handleUploadFile}
              className="flex items-center gap-2 text-slate-400 text-sm hover:text-slate-900 transition-colors"
            >
              {showUploadAnimation ? (
                <motion.div className="flex space-x-1" initial="hidden" animate="visible" variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.1 } } }}>
                  {[...Array(3)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="w-1.5 h-1.5 bg-blue-600 rounded-full"
                      variants={{ hidden: { opacity: 0, y: 5 }, visible: { opacity: 1, y: 0, transition: { duration: 0.4, repeat: Infinity, repeatType: "mirror", delay: i * 0.1 } } }}
                    />
                  ))}
                </motion.div>
              ) : (
                <Plus className="w-4 h-4" />
              )}
              <span>Upload Files</span>
            </button>
          </div>
        </div>

        {/* Command categories */}
        <div className="w-full grid grid-cols-3 gap-4 mb-4">
          <CommandButton
            icon={<BookOpen className="w-5 h-5" />}
            label="Learn"
            isActive={activeCommandCategory === "learn"}
            onClick={() => setActiveCommandCategory(activeCommandCategory === "learn" ? null : "learn")}
          />
          <CommandButton
            icon={<Code className="w-5 h-5" />}
            label="Code"
            isActive={activeCommandCategory === "code"}
            onClick={() => setActiveCommandCategory(activeCommandCategory === "code" ? null : "code")}
          />
          <CommandButton
            icon={<PenTool className="w-5 h-5" />}
            label="Write"
            isActive={activeCommandCategory === "write"}
            onClick={() => setActiveCommandCategory(activeCommandCategory === "write" ? null : "write")}
          />
        </div>

        {/* Command suggestions */}
        <AnimatePresence>
          {activeCommandCategory && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="w-full mb-6 overflow-hidden"
            >
              <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
                <div className="p-3 border-b border-border">
                  <h3 className="text-sm font-medium text-slate-900">
                    {activeCommandCategory === "learn"
                      ? "Learning suggestions"
                      : activeCommandCategory === "code"
                      ? "Coding suggestions"
                      : "Writing suggestions"}
                  </h3>
                </div>
                <ul className="divide-y divide-border">
                  {commandSuggestions[activeCommandCategory as keyof typeof commandSuggestions].map((suggestion, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: index * 0.03 }}
                      onClick={() => handleCommandSelect(suggestion)}
                      className="p-3 hover:bg-muted cursor-pointer transition-colors duration-75"
                    >
                      <div className="flex items-center gap-3">
                        {activeCommandCategory === "learn" ? (
                          <BookOpen className="w-4 h-4 text-blue-600" />
                        ) : activeCommandCategory === "code" ? (
                          <Code className="w-4 h-4 text-blue-600" />
                        ) : (
                          <PenTool className="w-4 h-4 text-blue-600" />
                        )}
                        <span className="text-sm text-slate-900">{suggestion}</span>
                      </div>
                    </motion.li>
                  ))}
                </ul>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

interface CommandButtonProps {
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  onClick: () => void;
}

function CommandButton({ icon, label, isActive, onClick }: CommandButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border transition-all ${
        isActive
          ? "bg-blue-50 border-blue-200 shadow-sm"
          : "bg-card border-border hover:border-muted-foreground/30"
      }`}
    >
      <div className={isActive ? "text-blue-600" : "text-slate-400"}>{icon}</div>
      <span className={`text-sm font-medium ${isActive ? "text-blue-700" : "text-slate-900"}`}>{label}</span>
    </motion.button>
  );
}
