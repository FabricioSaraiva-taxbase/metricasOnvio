"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

export type PeriodMode = "month" | "90d" | "180d" | "all" | "custom";

interface MonthOption {
    id: string;
    display: string;
    mes_raw: number;
}

interface FilterContextType {
    // Year/Month
    selectedYear: string;
    selectedMonth: string;
    setSelectedYear: (year: string) => void;
    setSelectedMonth: (month: string) => void;
    availableYears: string[];
    availableMonths: MonthOption[];

    // Period Mode
    periodMode: PeriodMode;
    setPeriodMode: (mode: PeriodMode) => void;
    customStartDate: string;
    customEndDate: string;
    setCustomStartDate: (date: string) => void;
    setCustomEndDate: (date: string) => void;

    // All months flat (for multi-month fetching)
    allMonthIds: string[];

    // Analyst & Client Filters
    selectedAnalyst: string;
    selectedClient: string;
    setSelectedAnalyst: (analyst: string) => void;
    setSelectedClient: (client: string) => void;

    // Department
    departments: Record<string, string>;
    selectedDepartment: string;
    setSelectedDepartment: (dept: string) => void;
    getDepartment: (analyst: string) => string;
    updateDepartment: (analyst: string, dept: string) => Promise<void>;

    // Refresh
    refreshKey: number;
    refreshData: () => void;

    isLoading: boolean;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
    const { isAuthenticated } = useAuth();

    const [selectedYear, setSelectedYear] = useState<string>("");
    const [selectedMonth, setSelectedMonth] = useState<string>("");
    const [availableYears, setAvailableYears] = useState<string[]>([]);
    const [availableMonths, setAvailableMonths] = useState<MonthOption[]>([]);
    const [allMonthIds, setAllMonthIds] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [refreshKey, setRefreshKey] = useState(0);

    // Period mode
    const [periodMode, setPeriodMode] = useState<PeriodMode>("month");
    const [customStartDate, setCustomStartDate] = useState<string>("");
    const [customEndDate, setCustomEndDate] = useState<string>("");

    // Analyst & Client
    const [selectedAnalyst, setSelectedAnalyst] = useState<string>("Todos");
    const [selectedClient, setSelectedClient] = useState<string>("Todos (Visão Geral)");

    // Departments
    const [departments, setDepartments] = useState<Record<string, string>>({});
    const [selectedDepartment, setSelectedDepartment] = useState<string>("Todos");

    const refreshData = useCallback(() => {
        setRefreshKey((prev) => prev + 1);
    }, []);

    // Fetch Departments
    useEffect(() => {
        if (!isAuthenticated) return;
        const fetchDepartments = async () => {
            try {
                const data = await api.get<Record<string, string>>("/api/departments");
                // Normalize keys to Uppercase
                const upperData: Record<string, string> = {};
                if (data) {
                    Object.entries(data).forEach(([k, v]) => {
                        upperData[k.toUpperCase()] = v;
                    });
                }
                setDepartments(upperData);
            } catch (error) {
                console.error("Error fetching departments:", error);
            }
        };
        fetchDepartments();
    }, [isAuthenticated, refreshKey]);

    const getDepartment = useCallback((analyst: string) => {
        return departments[analyst.toUpperCase()] || "Não Definido";
    }, [departments]);

    const updateDepartment = useCallback(async (analyst: string, dept: string) => {
        try {
            const upperAnalyst = analyst.toUpperCase();
            await api.post("/api/departments", { analyst: upperAnalyst, department: dept });
            setDepartments(prev => ({ ...prev, [upperAnalyst]: dept }));
        } catch (error) {
            console.error("Error updating department:", error);
            throw error;
        }
    }, []);

    useEffect(() => {
        if (!isAuthenticated) return;

        const fetchMonths = async () => {
            setIsLoading(true);
            try {
                const data = await api.get<{ data?: Record<string, any[]> }>("/api/data/list_months");

                if (data.data) {
                    const years = Object.keys(data.data).sort().reverse();
                    setAvailableYears(years);

                    // Collect ALL month IDs (flattened, sorted chronologically)
                    const allIds: string[] = [];
                    Object.keys(data.data)
                        .sort()
                        .forEach((year) => {
                            const monthsData = data.data![year] || [];
                            monthsData.forEach((m: any) => {
                                allIds.push(m.caminho || m.id);
                            });
                        });
                    setAllMonthIds(allIds);

                    if (years.length > 0) {
                        const firstYear = years[0];
                        if (!selectedYear) setSelectedYear(firstYear);

                        const targetYear = selectedYear || firstYear;
                        const monthsData = data.data[targetYear] || [];
                        const monthOptions: MonthOption[] = monthsData.map((m: any) => ({
                            id: m.caminho || m.id,
                            display: m.display,
                            mes_raw: m.mes_raw,
                        }));

                        setAvailableMonths(monthOptions);

                        if (monthOptions.length > 0 && !selectedMonth) {
                            setSelectedMonth(monthOptions[0].id);
                        }
                    }
                }
            } catch (error) {
                console.error("Error fetching months:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchMonths();
    }, [isAuthenticated, refreshKey]);

    // Update months when year changes
    useEffect(() => {
        if (!isAuthenticated || !selectedYear) return;

        const fetchMonthsForYear = async () => {
            try {
                const data = await api.get<{ data?: Record<string, any[]> }>("/api/data/list_months");

                if (data.data && data.data[selectedYear]) {
                    const monthsData = data.data[selectedYear];
                    const monthOptions: MonthOption[] = monthsData.map((m: any) => ({
                        id: m.caminho || m.id,
                        display: m.display,
                        mes_raw: m.mes_raw,
                    }));

                    setAvailableMonths(monthOptions);

                    if (monthOptions.length > 0) {
                        setSelectedMonth(monthOptions[0].id);
                    }
                }
            } catch (error) {
                console.error("Error fetching months for year:", error);
            }
        };

        fetchMonthsForYear();
    }, [selectedYear, isAuthenticated]);

    // Reset analyst/client filters when month changes
    useEffect(() => {
        setSelectedAnalyst("Todos");
        setSelectedClient("Todos (Visão Geral)");
        // setSelectedDepartment("Todos"); // Optional reset? Maybe keep it.
    }, [selectedMonth, periodMode]);

    return (
        <FilterContext.Provider
            value={{
                selectedYear,
                selectedMonth,
                setSelectedYear,
                setSelectedMonth,
                availableYears,
                availableMonths,
                periodMode,
                setPeriodMode,
                customStartDate,
                customEndDate,
                setCustomStartDate,
                setCustomEndDate,
                allMonthIds,
                selectedAnalyst,
                selectedClient,
                setSelectedAnalyst,
                setSelectedClient,

                // Departments
                departments,
                selectedDepartment,
                setSelectedDepartment,
                getDepartment,
                updateDepartment,

                refreshKey,
                refreshData,
                isLoading,
            }}
        >
            {children}
        </FilterContext.Provider>
    );
}

export function useFilter() {
    const context = useContext(FilterContext);
    if (context === undefined) {
        throw new Error("useFilter must be used within a FilterProvider");
    }
    return context;
}
