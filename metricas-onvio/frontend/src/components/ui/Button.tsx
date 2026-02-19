import * as React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "primary" | "secondary" | "danger" | "ghost";
    isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = "primary", isLoading, children, disabled, ...props }, ref) => {
        const variants = {
            primary: "bg-[#00A0E3] hover:bg-[#0080B3] text-white shadow-md shadow-blue-500/20",
            secondary: "bg-white dark:bg-[#282D33] border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800",
            danger: "bg-red-500 hover:bg-red-600 text-white",
            ghost: "bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300",
        };

        return (
            <button
                ref={ref}
                disabled={disabled || isLoading}
                className={cn(
                    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-[#00A0E3] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
                    variants[variant],
                    className
                )}
                {...props}
            >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {children}
            </button>
        );
    }
);
Button.displayName = "Button";
