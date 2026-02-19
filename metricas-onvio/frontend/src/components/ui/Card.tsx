import { cn } from "@/lib/utils";
import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    children?: React.ReactNode;
}

export function Card({ className, children, ...props }: CardProps) {
    return (
        <div
            className={cn(
                "bg-white dark:bg-[#282D33] border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm overflow-hidden",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}

export function CardHeader({ className, children, ...props }: CardProps) {
    return (
        <div
            className={cn("px-6 py-4 border-b border-gray-100 dark:border-gray-700/50", className)}
            {...props}
        >
            {children}
        </div>
    );
}

export function CardTitle({ className, children, ...props }: CardProps) {
    return (
        <h3
            className={cn("text-lg font-semibold text-gray-900 dark:text-white", className)}
            {...props}
        >
            {children}
        </h3>
    );
}

export function CardContent({ className, children, ...props }: CardProps) {
    return (
        <div className={cn("p-6", className)} {...props}>
            {children}
        </div>
    );
}
