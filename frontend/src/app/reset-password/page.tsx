'use client';

import { Suspense } from "react";
import AnimatedResetPasswordPage from "@/components/ui/animated-reset-password";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    }>
      <AnimatedResetPasswordPage />
    </Suspense>
  );
}
