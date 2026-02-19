/**
 * API Client — Wrapper do fetch com autenticação automática.
 * Injeta o header Authorization: Bearer <token> em todas as requisições.
 * Redireciona para /login em caso de 401.
 */

// Usamos caminho relativo para aproveitar o Proxy (Middleware) do Next.js
// Isso evita problemas de CORS e facilita configuração de ambiente (runtime variable)
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://metricas-backend-75142050260.us-central1.run.app";

interface ApiOptions extends RequestInit {
    skipAuth?: boolean;
}

class ApiClient {
    private getToken(): string | null {
        if (typeof window === "undefined") return null;
        return localStorage.getItem("taxbase_token");
    }

    private getHeaders(options?: ApiOptions): HeadersInit {
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
            ...(options?.headers as Record<string, string>),
        };

        if (!options?.skipAuth) {
            const token = this.getToken();
            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }
        }

        return headers;
    }

    private async handleResponse<T>(response: Response): Promise<T> {
        if (response.status === 401) {
            // Token expirado ou inválido
            if (typeof window !== "undefined") {
                localStorage.removeItem("taxbase_token");
                localStorage.removeItem("taxbase_user");
                window.location.href = "/login";
            }
            throw new Error("Sessão expirada. Faça login novamente.");
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Erro desconhecido" }));
            throw new Error(error.detail || `Erro ${response.status}`);
        }

        return response.json();
    }

    async get<T>(endpoint: string, options?: ApiOptions): Promise<T> {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "GET",
            headers: this.getHeaders(options),
            ...options,
        });
        return this.handleResponse<T>(response);
    }

    async post<T>(endpoint: string, body?: unknown, options?: ApiOptions): Promise<T> {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: this.getHeaders(options),
            body: body ? JSON.stringify(body) : undefined,
            ...options,
        });
        return this.handleResponse<T>(response);
    }

    async put<T>(endpoint: string, body?: unknown, options?: ApiOptions): Promise<T> {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "PUT",
            headers: this.getHeaders(options),
            body: body ? JSON.stringify(body) : undefined,
            ...options,
        });
        return this.handleResponse<T>(response);
    }

    async upload<T>(endpoint: string, formData: FormData, options?: ApiOptions): Promise<T> {
        const headers: Record<string, string> = {
            ...(options?.headers as Record<string, string>),
        };
        // Do NOT set Content-Type to multipart/form-data manually; browser does it with boundary

        if (!options?.skipAuth) {
            const token = this.getToken();
            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers,
            body: formData,
            ...options,
        });
        return this.handleResponse<T>(response);
    }

    async getPeriod<T>(months: string[], options?: ApiOptions): Promise<T> {
        return this.post<T>("/api/data/get_period", { months }, options);
    }
}

export const api = new ApiClient();
export { API_BASE };
