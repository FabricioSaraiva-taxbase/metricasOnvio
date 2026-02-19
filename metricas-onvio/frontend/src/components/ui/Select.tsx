"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

interface Option {
    value: string;
    label: string;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
    options: Option[];
    label?: string;
    containerClassName?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
    ({ className, containerClassName, options, label, ...props }, ref) => {
        return (
            <div className={cn("relative min-w-[140px]", containerClassName)}>
                {label && (
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                        {label}
                    </label>
                )}
                <div className="relative">
                    <select
                        className={cn(
                            "w-full appearance-none bg-white dark:bg-[#1E2328] border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-lg py-2 pl-3 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-[#00A0E3] focus:border-transparent transition-all cursor-pointer",
                            className
                        )}
                        ref={ref}
                        {...props}
                    >
                        {options.map((option) => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-2.5 h-4 w-4 text-gray-500 pointer-events-none" />
                </div>
            </div>
        );
    }
);
Select.displayName = "Select";
