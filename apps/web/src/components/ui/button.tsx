import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FF6B00] disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none",
  {
    variants: {
      variant: {
        default:
          "bg-[#161f30] text-[#f8fafc] border border-[#2d3b55] hover:bg-[#1e293b] active:bg-[#253347]",
        accent:
          "bg-[#ff6b00] text-white hover:bg-[#ff8533] active:bg-[#e05e00] shadow-[0_0_12px_rgba(255,107,0,0.25)]",
        outline:
          "border border-[#2d3b55] text-[#94a3b8] hover:text-[#f8fafc] hover:border-[#ff6b00] hover:bg-[#161f30]/60",
        ghost:
          "text-[#94a3b8] hover:text-[#f8fafc] hover:bg-[#1e293b]/70",
        destructive:
          "bg-[#ef4444]/20 text-[#ef4444] border border-[#dc2626]/60 hover:bg-[#ef4444]/30",
        subtleAccent:
          "bg-[rgba(255,107,0,0.12)] text-[#ff6b00] border border-[rgba(255,107,0,0.3)] hover:bg-[rgba(255,107,0,0.2)]",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-7 rounded px-3 text-xs",
        lg: "h-10 rounded-md px-6 text-base",
        icon: "h-8 w-8 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
