"use client";

import { useFilter, PeriodMode } from "@/contexts/FilterContext";
import { Select } from "@/components/ui/Select";
import { useMemo } from "react";

interface FilterBarProps {
    data?: any[];
    showPeriodSelector?: boolean;
}

const PERIOD_OPTIONS = [
    { value: "month", label: "Mês Individual" },
    { value: "90d", label: "Últimos 90 Dias" },
    { value: "180d", label: "Últimos 180 Dias" },
    { value: "all", label: "Período Completo" },
    { value: "custom", label: "Personalizado" },
];

export function FilterBar({ data, showPeriodSelector = true }: FilterBarProps) {
    const {
        selectedYear,
        selectedMonth,
        setSelectedYear,
        setSelectedMonth,
        availableYears,
        availableMonths,
        selectedAnalyst,
        selectedClient,
        setSelectedAnalyst,
        setSelectedClient,
        departments,
        selectedDepartment,
        setSelectedDepartment,
        periodMode,
        setPeriodMode,
        customStartDate,
        customEndDate,
        setCustomStartDate,
        setCustomEndDate,
        isLoading,
    } = useFilter();

    // Compute unique departments
    const uniqueDepartments = useMemo(() => {
        const values = Object.values(departments || {});
        return Array.from(new Set(values))
            .filter(Boolean)
            .sort();
    }, [departments]);

    // Derive analyst and client options from data
    const analysts = useMemo(() => {
        if (!data || data.length === 0) return [];
        const set = new Set<string>();
        data.forEach((item) => {
            if (item["Atendido por"]) set.add(String(item["Atendido por"]).trim());
        });
        return [...set].sort();
    }, [data]);

    const clients = useMemo(() => {
        if (!data || data.length === 0) return [];
        const EXCLUDED = ["TAXBASE INTERNO", "IGNORAR", "NÃO IDENTIFICADO"];
        const set = new Set<string>();
        data.forEach((item) => {
            const client = item.Cliente_Final || "";
            if (client && !EXCLUDED.includes(client)) set.add(client);
        });
        return [...set].sort();
    }, [data]);

    if (isLoading) {
        return (
            <div className="flex gap-4 items-end animate-pulse">
                <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                <div className="h-10 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg" />
            </div>
        );
    }

    return (
        <div className="flex flex-wrap gap-4 items-end">
            {/* Period Selector */}
            {showPeriodSelector && (
                <Select
                    label="Período"
                    value={periodMode}
                    onChange={(e) => setPeriodMode(e.target.value as PeriodMode)}
                    options={PERIOD_OPTIONS}
                />
            )}

            {/* Year/Month selectors only for single-month mode */}
            {periodMode === "month" && (
                <>
                    <Select
                        label="Ano"
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(e.target.value)}
                        options={availableYears.map((y) => ({ value: y, label: y }))}
                    />
                    <Select
                        label="Mês"
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(e.target.value)}
                        options={availableMonths.map((m) => ({
                            value: m.id,
                            label: m.display,
                        }))}
                    />
                </>
            )}

            {/* Custom date range inputs */}
            {periodMode === "custom" && (
                <>
                    <div className="relative min-w-[160px]">
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                            Data Início
                        </label>
                        <input
                            type="date"
                            value={customStartDate}
                            onChange={(e) => setCustomStartDate(e.target.value)}
                            className="w-full bg-white dark:bg-[#1E2328] border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-lg py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#00A0E3] focus:border-transparent transition-all"
                        />
                    </div>
                    <div className="relative min-w-[160px]">
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                            Data Fim
                        </label>
                        <input
                            type="date"
                            value={customEndDate}
                            onChange={(e) => setCustomEndDate(e.target.value)}
                            className="w-full bg-white dark:bg-[#1E2328] border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-lg py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#00A0E3] focus:border-transparent transition-all"
                        />
                    </div>
                </>
            )}

            {/* Department Filter */}
            {uniqueDepartments.length > 0 && (
                <Select
                    label="Departamento"
                    value={selectedDepartment}
                    onChange={(e) => setSelectedDepartment(e.target.value)}
                    options={[
                        { value: "Todos", label: "Todos" },
                        ...uniqueDepartments.map((d) => ({ value: d, label: d })),
                    ]}
                />
            )}

            {/* Analyst Filter */}
            {analysts.length > 0 && (
                <Select
                    label="Analista"
                    value={selectedAnalyst}
                    onChange={(e) => setSelectedAnalyst(e.target.value)}
                    options={[
                        { value: "Todos", label: "Todos" },
                        ...analysts.map((a) => ({ value: a, label: a })),
                    ]}
                />
            )}

            {/* Client Filter */}
            {clients.length > 0 && (
                <Select
                    label="Empresa"
                    value={selectedClient}
                    onChange={(e) => setSelectedClient(e.target.value)}
                    options={[
                        { value: "Todos (Visão Geral)", label: "Todos (Visão Geral)" },
                        ...clients.map((c) => ({ value: c, label: c })),
                    ]}
                />
            )}
        </div>
    );
}
