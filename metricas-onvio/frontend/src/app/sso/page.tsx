"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useAuth } from "@/components/AuthProvider";

/**
 * SSO Entry Point — /sso?token=XYZ
 *
 * Quando o Hub Taxbase redireciona para esta página:
 * 1. Lê o token JWT da query string
 * 2. Decodifica o payload (base64) para extrair dados do usuário
 * 3. Salva token e usuário no localStorage (mesmas chaves do AuthProvider)
 * 4. Marca origin como "hub" para exibir botão "Voltar ao Hub"
 * 5. Redireciona para o dashboard (/)
 */

function SSOHandler() {
    const { loginWithToken } = useAuth();
    const searchParams = useSearchParams();
    const router = useRouter();
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const token = searchParams.get("token");

        if (!token) {
            setError("Token não fornecido. Redirecionando para login...");
            setTimeout(() => router.replace("/login"), 2000);
            return;
        }

        try {
            // Decodificar o payload do JWT (parte central, base64url)
            const parts = token.split(".");
            if (parts.length !== 3) {
                throw new Error("Formato de token inválido");
            }

            const payload = JSON.parse(atob(parts[1]));

            // Extrair dados do usuário (formato Hub)
            const user = {
                username: payload.email || payload.sub || "unknown",
                role: mapHubPermission(payload.permissao || payload.role || "viewer"),
                nome: payload.nome || payload.email || payload.sub || "Usuário",
            };

            // Atualiza React state + localStorage via AuthProvider
            // (evita race condition onde localStorage é setado mas o state fica null)
            loginWithToken(token, user);
        } catch (err) {
            console.error("SSO Error:", err);
            setError("Erro ao processar token. Redirecionando para login...");
            setTimeout(() => router.replace("/login"), 2000);
        }
    }, [searchParams, router, loginWithToken]);

    return (
        <div
            style={{
                minHeight: "100vh",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background:
                    "linear-gradient(135deg, #0f1923 0%, #1a2a3a 30%, #0d2137 60%, #152535 100%)",
                color: "white",
                fontFamily: "var(--font-inter), sans-serif",
            }}
        >
            <div style={{ textAlign: "center" }}>
                {error ? (
                    <>
                        <div style={{ fontSize: "48px", marginBottom: "16px" }}>⚠️</div>
                        <p style={{ color: "#FCA5A5" }}>{error}</p>
                    </>
                ) : (
                    <>
                        <div
                            style={{
                                width: "48px",
                                height: "48px",
                                border: "3px solid rgba(0, 160, 227, 0.3)",
                                borderTopColor: "#00A0E3",
                                borderRadius: "50%",
                                animation: "spin 0.8s linear infinite",
                                margin: "0 auto 24px",
                            }}
                        />
                        <p style={{ color: "rgba(255, 255, 255, 0.7)", fontSize: "15px" }}>
                            Autenticando via Hub Taxbase...
                        </p>
                    </>
                )}
            </div>
            <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}

/** Mapeia permissões do Hub para roles do Metricas */
function mapHubPermission(permissao: string): string {
    if (permissao === "admin" || permissao === "admin_master") return "admin";
    return "viewer";
}

export default function SSOPage() {
    return (
        <Suspense
            fallback={
                <div
                    style={{
                        minHeight: "100vh",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "#0f1923",
                        color: "rgba(255,255,255,0.5)",
                    }}
                >
                    Carregando...
                </div>
            }
        >
            <SSOHandler />
        </Suspense>
    );
}
