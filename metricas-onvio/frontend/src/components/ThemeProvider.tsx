"use client";

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";

type Theme = "light" | "dark";

interface ThemeContextType {
    theme: Theme;
    toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setTheme] = useState<Theme>("light");
    const [mounted, setMounted] = useState(false);

    // Force 'dark' theme
    useEffect(() => {
        setTheme("dark");
        setMounted(true);
    }, []);

    // Aplica data-theme no <html>
    useEffect(() => {
        if (mounted) {
            document.documentElement.setAttribute("data-theme", "dark");
            localStorage.setItem("taxbase_theme", "dark");
        }
    }, [theme, mounted]);

    const toggleTheme = useCallback(() => {
        // Disabled
    }, []);

    // Evita flash de tema errado no SSR
    if (!mounted) {
        return <div style={{ visibility: "hidden" }}>{children}</div>;
    }

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error("useTheme deve ser usado dentro de <ThemeProvider>");
    }
    return context;
}
