import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex field-sizing-content min-h-16 w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-input)] px-2.5 py-2 text-base text-[var(--text-primary)] transition-colors outline-none placeholder:text-[var(--text-muted)] focus-visible:border-[var(--border-focus)] focus-visible:ring-3 focus-visible:ring-[var(--border-focus)]/50 disabled:cursor-not-allowed disabled:bg-[var(--bg-disabled)] disabled:opacity-50 aria-invalid:border-[var(--color-error)] aria-invalid:ring-3 aria-invalid:ring-[var(--color-error)]/20 md:text-sm dark:bg-[var(--bg-input)]/30 dark:disabled:bg-[var(--bg-input)]/80 dark:aria-invalid:border-[var(--color-error)]/50 dark:aria-invalid:ring-[var(--color-error)]/40",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
