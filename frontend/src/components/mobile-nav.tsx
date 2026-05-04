"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MessageSquare, FolderKanban, FileText, Bell, Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { icon: MessageSquare, label: "Chat", href: "/chat" },
  { icon: FolderKanban, label: "Tasks", href: "/tasks" },
  { icon: FileText, label: "Docs", href: "/documents" },
  { icon: Bell, label: "Alerts", href: "/notifications" },
];

export function MobileNav() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [activePath, setActivePath] = useState("/chat");

  return (
    <>
      {/* Bottom Tab Bar */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-50 lg:hidden">
        <div className="flex justify-around items-center h-16">
          {NAV_ITEMS.map((item) => {
            const isActive = activePath === item.href;
            return (
              <button
                key={item.label}
                onClick={() => {
                  setActivePath(item.href);
                  router.push(item.href);
                }}
                className={cn(
                  "flex flex-col items-center gap-1 py-2 px-4",
                  isActive ? "text-indigo-600" : "text-slate-400"
                )}
              >
                <item.icon className="w-5 h-5" />
                <span className="text-[10px] font-medium">{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Hamburger menu for additional options */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-20 right-4 w-12 h-12 bg-indigo-600 rounded-full shadow-lg flex items-center justify-center text-white z-50 lg:hidden"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>
    </>
  );
}
