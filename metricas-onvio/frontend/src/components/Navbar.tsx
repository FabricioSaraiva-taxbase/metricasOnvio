"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/components/AuthProvider";
import { useTheme } from "@/components/ThemeProvider";
import { useState, useEffect } from "react";

interface NavItem {
    label: string;
    href: string;
    adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
    { label: "Dashboard", href: "/" },
    { label: "Configurações", href: "/config", adminOnly: true },
];

export function Navbar() {
    const pathname = usePathname();
    const { user, logout } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [isFromHub, setIsFromHub] = useState(false);

    const hubUrl = process.env.NEXT_PUBLIC_HUB_URL || "https://hubtaxbase-354821232052.southamerica-east1.run.app";

    useEffect(() => {
        setIsFromHub(localStorage.getItem("taxbase_hub_origin") === "true");
    }, []);

    const visibleItems = NAV_ITEMS.filter(
        (item) => !item.adminOnly || user?.role === "admin"
    );

    return (
        <nav
            style={{
                height: "64px",
                padding: "0 24px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                borderBottom: "1px solid var(--border-color)",
                background: "var(--bg-card)",
                position: "sticky",
                top: 0,
                zIndex: 50,
                boxShadow: "var(--shadow-sm)",
            }}
        >
            {/* Left: Logo & Navigation */}
            <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
                {/* Logo */}
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{ position: "relative", width: "140px", height: "36px" }}>
                        <Image
                            src="/logo_taxbase.png"
                            alt="Taxbase Logo"
                            fill
                            style={{ objectFit: "contain", objectPosition: "left" }}
                            priority
                        />
                    </div>
                    <div
                        style={{
                            height: "24px",
                            width: "1px",
                            background: "var(--border-color)",
                        }}
                    />
                    <span
                        style={{
                            fontSize: "14px",
                            fontWeight: 500,
                            color: "var(--text-muted)",
                            letterSpacing: "0.5px",
                        }}
                    >
                        Métricas
                    </span>
                </div>

                {/* Navigation Links (Tabs) */}
                <div style={{ display: "flex", gap: "4px" }}>
                    {visibleItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                style={{
                                    padding: "8px 16px",
                                    borderRadius: "var(--radius-sm)",
                                    textDecoration: "none",
                                    fontSize: "14px",
                                    fontWeight: isActive ? 600 : 500,
                                    color: isActive ? "var(--taxbase-blue)" : "var(--text-secondary)",
                                    background: isActive ? "rgba(0, 160, 227, 0.08)" : "transparent",
                                    borderBottom: isActive ? "2px solid var(--taxbase-blue)" : "2px solid transparent",
                                    transition: "all var(--transition-fast)",
                                    display: "flex",
                                    alignItems: "center",
                                }}
                                onMouseEnter={(e) => {
                                    if (!isActive) {
                                        e.currentTarget.style.color = "var(--text-primary)";
                                        e.currentTarget.style.background = "var(--bg-secondary)";
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (!isActive) {
                                        e.currentTarget.style.color = "var(--text-secondary)";
                                        e.currentTarget.style.background = "transparent";
                                    }
                                }}
                            >
                                {item.label}
                            </Link>
                        );
                    })}
                </div>

                {/* Hub Return Button */}
                {isFromHub && (
                    <a
                        href={hubUrl}
                        style={{
                            padding: "6px 14px",
                            borderRadius: "var(--radius-sm)",
                            textDecoration: "none",
                            fontSize: "13px",
                            fontWeight: 500,
                            color: "var(--text-secondary)",
                            background: "rgba(0, 160, 227, 0.06)",
                            border: "1px solid rgba(0, 160, 227, 0.15)",
                            transition: "all var(--transition-fast)",
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            whiteSpace: "nowrap",
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = "rgba(0, 160, 227, 0.12)";
                            e.currentTarget.style.borderColor = "rgba(0, 160, 227, 0.3)";
                            e.currentTarget.style.color = "var(--taxbase-blue)";
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = "rgba(0, 160, 227, 0.06)";
                            e.currentTarget.style.borderColor = "rgba(0, 160, 227, 0.15)";
                            e.currentTarget.style.color = "var(--text-secondary)";
                        }}
                    >
                        ← Hub Taxbase
                    </a>
                )}
            </div>

            {/* Right: Controls */}
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                {/* Theme Toggle Removed */}
                {/* 
                <button
                    style={{ ... }}
                >
                    ...
                </button> 
                */}

                {/* User Profile Dropdown */}
                {user && (
                    <div style={{ position: "relative" }}>
                        <button
                            onClick={() => setIsProfileOpen(!isProfileOpen)}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "10px",
                                padding: "4px 8px 4px 4px",
                                borderRadius: "var(--radius-lg)",
                                background: "transparent",
                                border: "1px solid transparent",
                                cursor: "pointer",
                                transition: "all var(--transition-fast)",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.background = "var(--bg-secondary)";
                            }}
                            onMouseLeave={(e) => {
                                if (!isProfileOpen) e.currentTarget.style.background = "transparent";
                            }}
                        >
                            <div
                                style={{
                                    width: "32px",
                                    height: "32px",
                                    borderRadius: "50%",
                                    background: "linear-gradient(135deg, var(--taxbase-blue), var(--taxbase-blue-hover))",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    color: "white",
                                    fontSize: "14px",
                                    fontWeight: 700,
                                }}
                            >
                                {user.username.charAt(0).toUpperCase()}
                            </div>
                            <div style={{ textAlign: "left" }}>
                                <div
                                    style={{
                                        fontSize: "13px",
                                        fontWeight: 600,
                                        color: "var(--text-primary)",
                                        textTransform: "capitalize",
                                    }}
                                >
                                    {user.username}
                                </div>
                                <div
                                    style={{
                                        fontSize: "10px",
                                        color: "var(--text-muted)",
                                        textTransform: "uppercase",
                                        letterSpacing: "0.5px",
                                    }}
                                >
                                    {user.role}
                                </div>
                            </div>
                            <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>▼</span>
                        </button>

                        {/* Dropdown Menu */}
                        {isProfileOpen && (
                            <>
                                <div
                                    style={{
                                        position: "fixed",
                                        top: 0,
                                        left: 0,
                                        right: 0,
                                        bottom: 0,
                                        zIndex: 40,
                                    }}
                                    onClick={() => setIsProfileOpen(false)}
                                />
                                <div
                                    className="animate-fade-in"
                                    style={{
                                        position: "absolute",
                                        top: "100%",
                                        right: 0,
                                        marginTop: "8px",
                                        width: "160px",
                                        background: "var(--bg-card)",
                                        border: "1px solid var(--border-color)",
                                        borderRadius: "var(--radius-md)",
                                        boxShadow: "var(--shadow-md)",
                                        padding: "4px",
                                        zIndex: 50,
                                    }}
                                >
                                    <button
                                        onClick={logout}
                                        style={{
                                            width: "100%",
                                            padding: "8px 12px",
                                            borderRadius: "var(--radius-sm)",
                                            background: "transparent",
                                            border: "none",
                                            cursor: "pointer",
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "8px",
                                            fontSize: "13px",
                                            color: "#EF4444",
                                            transition: "all var(--transition-fast)",
                                            textAlign: "left",
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.background = "transparent";
                                        }}
                                    >
                                        🚪 Sair
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                )}
            </div>
        </nav>
    );
}
