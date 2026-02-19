"use client";

import { useState } from "react";
import Image from "next/image";
import { useAuth } from "@/components/AuthProvider";

export default function LoginPage() {
    const { login } = useAuth();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (!username.trim() || !password.trim()) {
            setError("Preencha todos os campos.");
            return;
        }

        setIsLoading(true);
        try {
            await login(username, password);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Credenciais inválidas. Tente novamente."
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div
            style={{
                minHeight: "100vh",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background:
                    "linear-gradient(135deg, #0f1923 0%, #1a2a3a 30%, #0d2137 60%, #152535 100%)",
                backgroundSize: "200% 200%",
                animation: "gradient-shift 15s ease infinite",
                position: "relative",
                overflow: "hidden",
            }}
        >
            {/* Decorative orbs */}
            <div
                style={{
                    position: "absolute",
                    top: "-10%",
                    right: "-5%",
                    width: "500px",
                    height: "500px",
                    borderRadius: "50%",
                    background: "radial-gradient(circle, rgba(0,160,227,0.08) 0%, transparent 70%)",
                    pointerEvents: "none",
                }}
            />
            <div
                style={{
                    position: "absolute",
                    bottom: "-15%",
                    left: "-10%",
                    width: "600px",
                    height: "600px",
                    borderRadius: "50%",
                    background: "radial-gradient(circle, rgba(0,160,227,0.05) 0%, transparent 70%)",
                    pointerEvents: "none",
                }}
            />

            {/* Login Card */}
            <div
                className="animate-fade-in"
                style={{
                    width: "100%",
                    maxWidth: "420px",
                    padding: "48px 40px",
                    position: "relative",
                    zIndex: 1,
                }}
            >
                {/* Logo */}
                <div style={{ textAlign: "center", marginBottom: "48px" }}>
                    <div
                        style={{
                            position: "relative",
                            width: "240px",
                            height: "80px",
                            margin: "0 auto 16px",
                            filter: "drop-shadow(0 0 20px rgba(0, 160, 227, 0.3))",
                        }}
                    >
                        <Image
                            src="/logo_taxbase.png"
                            alt="Taxbase Logo"
                            fill
                            style={{ objectFit: "contain" }}
                            priority
                        />
                    </div>
                    <p
                        style={{
                            color: "rgba(255, 255, 255, 0.4)",
                            fontSize: "14px",
                            margin: 0,
                            letterSpacing: "1px",
                            fontWeight: 500,
                        }}
                    >
                        Painel de Métricas
                    </p>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit}>
                    {/* Username */}
                    <div style={{ marginBottom: "16px" }}>
                        <label
                            htmlFor="username"
                            style={{
                                display: "block",
                                fontSize: "13px",
                                fontWeight: 500,
                                color: "rgba(255, 255, 255, 0.7)",
                                marginBottom: "8px",
                            }}
                        >
                            👤 Usuário
                        </label>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Digite seu usuário"
                            autoComplete="username"
                            style={{
                                width: "100%",
                                padding: "14px 16px",
                                borderRadius: "12px",
                                border: "1px solid rgba(0, 160, 227, 0.2)",
                                background: "rgba(255, 255, 255, 0.92)",
                                color: "#1E2328",
                                fontSize: "15px",
                                outline: "none",
                                transition: "all 250ms ease",
                                boxSizing: "border-box",
                            }}
                            onFocus={(e) => {
                                e.currentTarget.style.borderColor = "#00A0E3";
                                e.currentTarget.style.boxShadow =
                                    "0 0 0 3px rgba(0, 160, 227, 0.15)";
                                e.currentTarget.style.background = "#FFFFFF";
                            }}
                            onBlur={(e) => {
                                e.currentTarget.style.borderColor = "rgba(0, 160, 227, 0.2)";
                                e.currentTarget.style.boxShadow = "none";
                                e.currentTarget.style.background = "rgba(255, 255, 255, 0.92)";
                            }}
                        />
                    </div>

                    {/* Password */}
                    <div style={{ marginBottom: "24px" }}>
                        <label
                            htmlFor="password"
                            style={{
                                display: "block",
                                fontSize: "13px",
                                fontWeight: 500,
                                color: "rgba(255, 255, 255, 0.7)",
                                marginBottom: "8px",
                            }}
                        >
                            🔒 Senha
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Digite sua senha"
                            autoComplete="current-password"
                            style={{
                                width: "100%",
                                padding: "14px 16px",
                                borderRadius: "12px",
                                border: "1px solid rgba(0, 160, 227, 0.2)",
                                background: "rgba(255, 255, 255, 0.92)",
                                color: "#1E2328",
                                fontSize: "15px",
                                outline: "none",
                                transition: "all 250ms ease",
                                boxSizing: "border-box",
                            }}
                            onFocus={(e) => {
                                e.currentTarget.style.borderColor = "#00A0E3";
                                e.currentTarget.style.boxShadow =
                                    "0 0 0 3px rgba(0, 160, 227, 0.15)";
                                e.currentTarget.style.background = "#FFFFFF";
                            }}
                            onBlur={(e) => {
                                e.currentTarget.style.borderColor = "rgba(0, 160, 227, 0.2)";
                                e.currentTarget.style.boxShadow = "none";
                                e.currentTarget.style.background = "rgba(255, 255, 255, 0.92)";
                            }}
                        />
                    </div>

                    {/* Error message */}
                    {error && (
                        <div
                            className="animate-fade-in"
                            style={{
                                padding: "12px 16px",
                                borderRadius: "10px",
                                background: "rgba(239, 68, 68, 0.1)",
                                border: "1px solid rgba(239, 68, 68, 0.3)",
                                color: "#FCA5A5",
                                fontSize: "13px",
                                marginBottom: "16px",
                                textAlign: "center",
                            }}
                        >
                            ❌ {error}
                        </div>
                    )}

                    {/* Submit button */}
                    <button
                        type="submit"
                        disabled={isLoading}
                        style={{
                            width: "100%",
                            padding: "14px",
                            borderRadius: "12px",
                            border: "none",
                            background: isLoading
                                ? "rgba(0, 160, 227, 0.5)"
                                : "linear-gradient(135deg, #00A0E3 0%, #0080B3 100%)",
                            color: "white",
                            fontSize: "16px",
                            fontWeight: 700,
                            letterSpacing: "0.5px",
                            cursor: isLoading ? "not-allowed" : "pointer",
                            transition: "all 300ms ease",
                            boxShadow: "0 4px 20px rgba(0, 160, 227, 0.35)",
                        }}
                        onMouseEnter={(e) => {
                            if (!isLoading) {
                                e.currentTarget.style.transform = "translateY(-2px)";
                                e.currentTarget.style.boxShadow =
                                    "0 8px 30px rgba(0, 160, 227, 0.5)";
                            }
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = "translateY(0)";
                            e.currentTarget.style.boxShadow =
                                "0 4px 20px rgba(0, 160, 227, 0.35)";
                        }}
                    >
                        {isLoading ? "Autenticando..." : "Entrar →"}
                    </button>
                </form>

                {/* Footer */}
                <p
                    style={{
                        textAlign: "center",
                        color: "rgba(255, 255, 255, 0.2)",
                        fontSize: "12px",
                        marginTop: "32px",
                    }}
                >
                    © 2025 Taxbase · Todos os direitos reservados
                </p>
            </div>
        </div>
    );
}
