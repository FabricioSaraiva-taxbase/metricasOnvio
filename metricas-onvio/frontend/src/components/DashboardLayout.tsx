"use client";

import { useAuth } from "@/components/AuthProvider";
import { Navbar } from "@/components/Navbar";
import type { ReactNode } from "react";

export function DashboardLayout({ children }: { children: ReactNode }) {
    const { isAuthenticated, isLoading } = useAuth();

    // Loading state
    if (isLoading) {
        return (
            <div
                style={{
                    width: "100vw",
                    height: "100vh",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "var(--bg-primary)",
                }}
            >
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: "16px",
                    }}
                >
                    <div
                        style={{
                            width: "48px",
                            height: "48px",
                            border: "3px solid var(--border-color)",
                            borderTopColor: "var(--taxbase-blue)",
                            borderRadius: "50%",
                            animation: "spin 0.8s linear infinite",
                        }}
                    />
                    <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
                        Carregando...
                    </p>
                    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                </div>
            </div>
        );
    }

    // Not authenticated — AuthProvider handles redirect
    if (!isAuthenticated) {
        return null;
    }

    return (
        <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
            <Navbar />
            <main
                style={{
                    flex: 1,
                    padding: "32px",
                    maxWidth: "1600px",
                    width: "100%",
                    margin: "0 auto",
                }}
                className="animate-fade-in"
            >
                {children}
            </main>
        </div>
    );
}
