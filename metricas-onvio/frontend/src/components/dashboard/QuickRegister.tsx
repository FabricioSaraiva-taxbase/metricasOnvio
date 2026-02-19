"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import { ChevronDown, ChevronUp, UserPlus } from "lucide-react";

interface QuickRegisterProps {
    data: any[];
    onRegistered?: () => void;
}

const EXCLUDED_CLIENTS = ["NÃO IDENTIFICADO", "TAXBASE INTERNO", "IGNORAR", "DESCONHECIDO", ""];

export function QuickRegister({ data, onRegistered }: QuickRegisterProps) {
    const { user } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const [selectedContact, setSelectedContact] = useState("");
    const [clientName, setClientName] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(e.target as Node) &&
                inputRef.current &&
                !inputRef.current.contains(e.target as Node)
            ) {
                setShowSuggestions(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Get unidentified contacts (computed before hooks that depend on data)
    const unidentified = data?.filter((item) => item.Cliente_Final === "NÃO IDENTIFICADO") || [];
    const uniqueContacts = [...new Set(unidentified.map((item) => String(item.Contato || "").trim()).filter(Boolean))].sort();

    // Extract all unique company names from the data (excluding system values)
    const uniqueCompanies = useMemo(() => {
        const companies = new Set<string>();
        data?.forEach((item) => {
            const name = String(item.Cliente_Final || "").trim().toUpperCase();
            if (name && !EXCLUDED_CLIENTS.includes(name)) {
                companies.add(name);
            }
        });
        return [...companies].sort();
    }, [data]);

    // Filter suggestions based on what the user has typed
    const filteredSuggestions = useMemo(() => {
        const query = clientName.trim().toUpperCase();
        if (!query) return uniqueCompanies;
        return uniqueCompanies.filter((c) => c.startsWith(query));
    }, [clientName, uniqueCompanies]);

    // Only show for admins
    if (user?.role !== "admin") return null;

    // Nothing to show if no unidentified contacts
    if (unidentified.length === 0) return null;

    const handleRegister = async () => {
        if (!selectedContact || !clientName.trim()) return;

        setIsLoading(true);
        setFeedback(null);

        try {
            await api.post("/api/admin/register_client", {
                nome_contato: selectedContact,
                nome_cliente: clientName.trim().toUpperCase(),
            });
            setFeedback({ type: "success", text: `Vinculado: ${selectedContact} → ${clientName.toUpperCase()}` });
            setSelectedContact("");
            setClientName("");
            setShowSuggestions(false);
            onRegistered?.();
        } catch (error) {
            setFeedback({
                type: "error",
                text: error instanceof Error ? error.message : "Erro ao vincular.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelectSuggestion = (company: string) => {
        setClientName(company);
        setShowSuggestions(false);
    };

    return (
        <div className="rounded-xl border border-amber-200 dark:border-amber-800/40 bg-amber-50/50 dark:bg-amber-900/10">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full px-5 py-3 flex items-center justify-between text-sm font-medium text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors"
            >
                <span className="flex items-center gap-2">
                    🚨 Há <strong>{unidentified.length}</strong> atendimentos &quot;NÃO IDENTIFICADO&quot; — vincular agora
                </span>
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {isOpen && (
                <div className="px-5 pb-4 border-t border-amber-200 dark:border-amber-800/30 pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                        <div>
                            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                Contato
                            </label>
                            <select
                                value={selectedContact}
                                onChange={(e) => setSelectedContact(e.target.value)}
                                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#1E2328] text-gray-900 dark:text-white"
                            >
                                <option value="">Selecione...</option>
                                {uniqueContacts.map((c) => (
                                    <option key={c} value={c}>{c}</option>
                                ))}
                            </select>
                        </div>
                        <div className="relative">
                            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                Nome da Empresa
                            </label>
                            <input
                                ref={inputRef}
                                type="text"
                                value={clientName}
                                onChange={(e) => {
                                    setClientName(e.target.value);
                                    setShowSuggestions(true);
                                }}
                                onFocus={() => setShowSuggestions(true)}
                                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#1E2328] text-gray-900 dark:text-white"
                            />
                            {showSuggestions && filteredSuggestions.length > 0 && (
                                <div
                                    ref={dropdownRef}
                                    className="absolute z-50 left-0 right-0 mt-1 max-h-48 overflow-y-auto rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-[#1E2328] shadow-lg"
                                >
                                    {filteredSuggestions.map((company) => (
                                        <button
                                            key={company}
                                            type="button"
                                            onClick={() => handleSelectSuggestion(company)}
                                            className="w-full text-left px-3 py-2 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                                        >
                                            {company}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <button
                            onClick={handleRegister}
                            disabled={!selectedContact || !clientName.trim() || isLoading}
                            className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[#00A0E3] text-white hover:bg-[#0089c2] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <UserPlus className="h-4 w-4" />
                            {isLoading ? "Salvando..." : "Vincular"}
                        </button>
                    </div>

                    {feedback && (
                        <div className={`mt-3 text-sm p-2 rounded-lg ${feedback.type === "success"
                            ? "bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300"
                            : "bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300"
                            }`}>
                            {feedback.text}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

