import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "default" | "outline" | "ghost" };

export function Button({ className, variant = "default", ...props }: Props) {
  return <button className={cn("inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700 disabled:pointer-events-none disabled:opacity-50", variant === "default" && "bg-teal-800 text-white hover:bg-teal-900", variant === "outline" && "border border-slate-300 bg-white text-slate-800 hover:bg-slate-50", variant === "ghost" && "text-slate-600 hover:bg-slate-100", className)} {...props} />;
}
