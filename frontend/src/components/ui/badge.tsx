import { mergeProps } from "@base-ui/react/merge-props"
import { useRender } from "@base-ui/react/use-render"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "group/badge inline-flex h-5 w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-4xl border border-transparent px-2 py-0.5 text-xs font-medium whitespace-nowrap transition-all focus-visible:border-[var(--border-focus)] focus-visible:ring-[3px] focus-visible:ring-[var(--border-focus)]/50 has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 aria-invalid:border-[var(--color-error)] aria-invalid:ring-[var(--color-error)]/20 dark:aria-invalid:ring-[var(--color-error)]/40 [&>svg]:pointer-events-none [&>svg]:size-3!",
  {
    variants: {
      variant: {
        default: "bg-[var(--brand-primary)] text-[var(--text-inverse)] [a]:hover:bg-[var(--brand-primary-hover)]",
        secondary:
          "bg-[var(--bg-elevated)] text-[var(--text-secondary)] [a]:hover:bg-[var(--bg-elevated-hover)]",
        destructive:
          "bg-[var(--color-error)]/10 text-[var(--color-error)] focus-visible:ring-[var(--color-error)]/20 dark:bg-[var(--color-error)]/20 dark:focus-visible:ring-[var(--color-error)]/40 [a]:hover:bg-[var(--color-error)]/20",
        outline:
          "border-[var(--border-default)] text-[var(--text-primary)] [a]:hover:bg-[var(--bg-subtle)] [a]:hover:text-[var(--text-primary)]",
        ghost:
          "hover:bg-[var(--bg-subtle)] hover:text-[var(--text-secondary)] dark:hover:bg-[var(--bg-subtle)]/50",
        link: "text-[var(--text-link)] underline-offset-4 hover:underline",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  render,
  ...props
}: useRender.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return useRender({
    defaultTagName: "span",
    props: mergeProps<"span">(
      {
        className: cn(badgeVariants({ variant }), className),
      },
      props
    ),
    render,
    state: {
      slot: "badge",
      variant,
    },
  })
}

export { Badge, badgeVariants }
