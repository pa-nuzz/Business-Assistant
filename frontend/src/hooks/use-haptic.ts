"use client";

export function useHaptic() {
  const trigger = (type: "success" | "error" | "warning" | "light" = "light") => {
    if (typeof navigator === "undefined" || !("vibrate" in navigator)) return;

    switch (type) {
      case "success":
        navigator.vibrate([50, 30, 50]);
        break;
      case "error":
        navigator.vibrate([100, 50, 100]);
        break;
      case "warning":
        navigator.vibrate([30, 20, 30]);
        break;
      default:
        navigator.vibrate(20);
    }
  };

  return { trigger };
}
