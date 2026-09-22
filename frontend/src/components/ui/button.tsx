"use client"

import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-lg border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all outline-none select-none cursor-pointer focus-visible:ring-2 focus-visible:ring-[var(--border-focus)]/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-base)] active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-[var(--color-error)] aria-invalid:ring-2 aria-invalid:ring-[var(--color-error)]/20 dark:aria-invalid:border-[var(--color-error)]/50 dark:aria-invalid:ring-[var(--color-error)]/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-[var(--brand-primary)] text-[var(--text-inverse)] [a]:hover:bg-[var(--brand-primary-hover)]",
        outline:
          "border-[var(--border-default)] bg-[var(--bg-base)] hover:bg-[var(--bg-subtle)] hover:text-[var(--text-primary)] aria-expanded:bg-[var(--bg-subtle)] aria-expanded:text-[var(--text-primary)] dark:border-[var(--border-subtle)] dark:bg-[var(--bg-input)]/30 dark:hover:bg-[var(--bg-input)]/50",
        secondary:
          "bg-[var(--bg-elevated)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated-hover)] aria-expanded:bg-[var(--bg-elevated-hover)] aria-expanded:text-[var(--text-primary)]",
        ghost:
          "hover:bg-[var(--bg-subtle)] hover:text-[var(--text-primary)] aria-expanded:bg-[var(--bg-subtle)] aria-expanded:text-[var(--text-primary)] dark:hover:bg-[var(--bg-subtle)]/50",
        destructive:
          "bg-[var(--color-error)]/10 text-[var(--color-error)] hover:bg-[var(--color-error)]/20 focus-visible:border-[var(--color-error)]/40 focus-visible:ring-[var(--color-error)]/20 dark:bg-[var(--color-error)]/20 dark:hover:bg-[var(--color-error)]/30 dark:focus-visible:ring-[var(--color-error)]/40",
        link: "text-[var(--text-link)] underline-offset-4 hover:underline",
      },
      size: {
        default:
          "h-8 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
        xs: "h-6 gap-1 rounded-[min(var(--radius-md),10px)] px-2 text-xs in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-7 gap-1 rounded-[min(var(--radius-md),12px)] px-2.5 text-[0.8rem] in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-9 gap-1.5 px-2.5 has-data-[icon=inline-end]:pr-3 has-data-[icon=inline-start]:pl-3",
        icon: "size-8",
        "icon-xs":
          "size-6 rounded-[min(var(--radius-md),10px)] in-data-[slot=button-group]:rounded-lg [&_svg:not([class*='size-'])]:size-3",
        "icon-sm":
          "size-7 rounded-[min(var(--radius-md),12px)] in-data-[slot=button-group]:rounded-lg",
        "icon-lg": "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
