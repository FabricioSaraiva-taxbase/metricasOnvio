"use client";

import {
    createContext,
    useContext,
    useEffect,
    useState,
    useCallback,
    type ReactNode,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import { api } from "@/lib/api";

interface User {
    username: string;
    role: string;
    nome?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    loginWithToken: (jwt: string, userData: User) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Rotas que não precisam de autenticação
const PUBLIC_ROUTES = ["/login", "/sso"];

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    // Carrega sessão do localStorage na montagem
    useEffect(() => {
        const storedToken = localStorage.getItem("taxbase_token");
        const storedUser = localStorage.getItem("taxbase_user");

        if (storedToken && storedUser) {
            try {
                setToken(storedToken);
                setUser(JSON.parse(storedUser));
            } catch {
                localStorage.removeItem("taxbase_token");
                localStorage.removeItem("taxbase_user");
            }
        }
        setIsLoading(false);
    }, []);

    // Redireciona para /login se não autenticado em rota protegida
    useEffect(() => {
        if (!isLoading && !token && !PUBLIC_ROUTES.includes(pathname)) {
            router.replace("/login");
        }
    }, [isLoading, token, pathname, router]);

    const login = useCallback(
        async (username: string, password: string) => {
            const response = await api.post<{
                access_token: string;
                token_type: string;
                user_role: string;
            }>("/api/auth/login", { username, password }, { skipAuth: true });

            const newUser: User = { username, role: response.user_role };

            localStorage.setItem("taxbase_token", response.access_token);
            localStorage.setItem("taxbase_user", JSON.stringify(newUser));

            setToken(response.access_token);
            setUser(newUser);

            router.push("/");
        },
        [router]
    );

    const loginWithToken = useCallback(
        (jwt: string, userData: User) => {
            localStorage.setItem("taxbase_token", jwt);
            localStorage.setItem("taxbase_user", JSON.stringify(userData));
            localStorage.setItem("taxbase_hub_origin", "true");
            setToken(jwt);
            setUser(userData);
            router.replace("/");
        },
        [router]
    );

    const logout = useCallback(() => {
        // Ler flag ANTES de limpar
        const wasHub = localStorage.getItem("taxbase_hub_origin");
        const hubUrl = process.env.NEXT_PUBLIC_HUB_URL || "https://hubtaxbase-354821232052.southamerica-east1.run.app";

        localStorage.removeItem("taxbase_token");
        localStorage.removeItem("taxbase_user");
        localStorage.removeItem("taxbase_hub_origin");
        setToken(null);
        setUser(null);

        // Se veio do Hub, voltar para lá
        if (wasHub) {
            window.location.href = hubUrl;
        } else {
            router.push("/login");
        }
    }, [router]);

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isAuthenticated: !!token,
                isLoading,
                login,
                loginWithToken,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
    }
    return context;
}
