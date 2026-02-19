"use client";

import { useMemo, useState, useEffect } from "react";
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { format, eachDayOfInterval, endOfMonth, startOfMonth, parseISO, isValid } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Calendar } from "lucide-react";

interface EvolutionChartProps {
    data: any[];
    year: number;
    month: number;
    isLoading?: boolean;
}

export function EvolutionChart({ data, year, month, isLoading }: EvolutionChartProps) {
    const [showFullCalendar, setShowFullCalendar] = useState(true);
    const [isMultiMonth, setIsMultiMonth] = useState(false);

    // Detect if data spans multiple months
    useEffect(() => {
        if (!data || data.length === 0) return;

        const uniqueMonths = new Set();
        data.forEach(item => {
            const dateStr = item.Dia || item.Data?.split("T")[0];
            if (dateStr && dateStr.length >= 7) {
                uniqueMonths.add(dateStr.substring(0, 7)); // YYYY-MM
            }
        });

        const multi = uniqueMonths.size > 1;
        setIsMultiMonth(multi);

        // Auto-disable full calendar if multi-month
        if (multi) {
            setShowFullCalendar(false);
        } else {
            // Reset to true only if we haven't touched it? 
            // Ideally we want single month -> default true.
            // But let's just default to true if it goes back to single month.
            setShowFullCalendar(true);
        }
    }, [data]);

    const chartData = useMemo(() => {
        // Safety check
        if (!data) return [];

        // Group actual data by Date
        const grouped: Record<string, number> = {};
        data.forEach((item) => {
            const dateStr = item.Dia || item.Data?.split("T")[0];
            if (dateStr) {
                grouped[dateStr] = (grouped[dateStr] || 0) + 1;
            }
        });

        // 1. Single Month with Full Calendar Mode
        if (showFullCalendar && !isMultiMonth && year && month) {
            try {
                const startDate = startOfMonth(new Date(year, month - 1, 1));
                const endDate = endOfMonth(startDate);
                const allDays = eachDayOfInterval({ start: startDate, end: endDate });

                return allDays.map((day) => {
                    const dateKey = format(day, "yyyy-MM-dd");
                    return {
                        date: dateKey,
                        count: grouped[dateKey] || 0,
                        label: format(day, "dd/MM", { locale: ptBR }),
                        dayNum: format(day, "d"), // 1, 2, 3...
                        fullDate: day,
                    };
                });
            } catch (e) {
                console.error("Error generating calendar:", e);
                return [];
            }
        }

        // 2. Multi-month OR Single Month (Timeline Mode)
        // Just show the days that have data (or we could fill gaps if we wanted to be fancy, but simple is better for now)
        // For multi-month, we definitely want linear time.

        return Object.entries(grouped)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([dateKey, count]) => {
                let day: Date;
                try {
                    day = parseISO(dateKey);
                    if (!isValid(day)) throw new Error("Invalid date");
                } catch {
                    day = new Date(dateKey + "T12:00:00");
                }

                return {
                    date: dateKey,
                    count,
                    label: isValid(day) ? format(day, "dd/MM", { locale: ptBR }) : dateKey,
                    dayNum: isValid(day) ? format(day, "dd/MM") : dateKey, // Show dd/MM on X axis for multi-month
                    fullDate: day,
                };
            });

    }, [data, year, month, showFullCalendar, isMultiMonth]);

    if (isLoading) {
        return (
            <Card className="col-span-1 lg:col-span-2 h-[400px]">
                <CardHeader>
                    <CardTitle>Atendimentos por Dia</CardTitle>
                </CardHeader>
                <CardContent className="h-[320px] flex items-center justify-center">
                    <div className="h-full w-full bg-gray-100 dark:bg-gray-800 animate-pulse rounded-lg" />
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="col-span-1 lg:col-span-2 h-[400px]" style={{ background: 'var(--bg-card)' }}>
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Atendimentos por Dia</CardTitle>

                {/* Only show calendar toggle if single month */}
                {!isMultiMonth && (
                    <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-500 dark:text-gray-400 font-normal">
                        <input
                            type="checkbox"
                            checked={showFullCalendar}
                            onChange={(e) => setShowFullCalendar(e.target.checked)}
                            className="w-4 h-4 rounded accent-[#00A0E3]"
                        />
                        <Calendar className="h-3.5 w-3.5" />
                        Calendário completo
                    </label>
                )}
            </CardHeader>
            <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--chart-grid)" opacity={0.5} />
                        <XAxis
                            dataKey="dayNum"
                            stroke="var(--chart-axis)"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => val}
                            minTickGap={15}
                        />
                        <YAxis
                            stroke="var(--chart-axis)"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(value) => `${value}`}
                        />
                        <Tooltip
                            cursor={{ fill: "transparent" }}
                            contentStyle={{
                                backgroundColor: "var(--bg-card)",
                                borderColor: "var(--border-color)",
                                borderRadius: "8px",
                                color: "var(--text-primary)",
                            }}
                            formatter={(value: number | undefined) => [`${value ?? 0} atendimentos`, "Volume"]}
                            labelFormatter={(label, payload) => {
                                if (payload && payload.length > 0) {
                                    return payload[0].payload.label;
                                }
                                return label;
                            }}
                        />
                        <Bar
                            dataKey="count"
                            fill="#00A0E3"
                            radius={[4, 4, 0, 0] as [number, number, number, number]}
                            maxBarSize={50}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
