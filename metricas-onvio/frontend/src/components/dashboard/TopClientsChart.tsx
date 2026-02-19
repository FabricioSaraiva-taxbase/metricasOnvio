"use client";

import { useMemo, useState } from "react";
import { useFilter } from "@/contexts/FilterContext";
import {
    ResponsiveContainer,
    ComposedChart,
    Bar,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    LabelList,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { ChevronDown, ChevronUp } from "lucide-react";

interface TopClientsChartProps {
    data: any[];
    isLoading?: boolean;
}

export function TopClientsChart({ data, isLoading }: TopClientsChartProps) {
    const { getDepartment } = useFilter();
    const [showFullRanking, setShowFullRanking] = useState(false);

    const { chartData, fullRanking, allDepts } = useMemo(() => {
        if (!data || data.length === 0) return { chartData: [], fullRanking: [], allDepts: [] };

        const EXCLUDED = ["TAXBASE INTERNO", "IGNORAR", "NÃO IDENTIFICADO"];
        const deptSet = new Set<string>();

        // { ClientName: { total: 0, [Dept]: 0 } }
        const grouped: Record<string, any> = {};

        data.forEach((item) => {
            const client = item.Cliente_Final || item.CLIENTE || "DESCONHECIDO";
            if (!EXCLUDED.includes(client)) {
                if (!grouped[client]) grouped[client] = { name: client, total: 0 };

                const analyst = String(item["Atendido por"] || "").toUpperCase();
                const dept = getDepartment(analyst) || "Não Definido";

                grouped[client][dept] = (grouped[client][dept] || 0) + 1;
                grouped[client].total += 1;
                deptSet.add(dept);
            }
        });

        // Convert to array and sort by total
        const sorted = Object.values(grouped).sort((a: any, b: any) => b.total - a.total);

        const top10 = sorted.slice(0, 10).map((item: any) => ({
            ...item,
            shortName: item.name.length > 20 ? item.name.substring(0, 20) + "..." : item.name,
            fullName: item.name,
        }));

        const allDepts = Array.from(deptSet).sort();
        // Priorities: DP, Fiscal, Contábil first
        const priority = ["Fiscal", "Contábil", "DP", "Fernando"];
        allDepts.sort((a, b) => {
            const idxA = priority.indexOf(a);
            const idxB = priority.indexOf(b);
            if (idxA !== -1 && idxB !== -1) return idxA - idxB;
            if (idxA !== -1) return -1;
            if (idxB !== -1) return 1;
            return a.localeCompare(b);
        });

        return { chartData: top10, fullRanking: sorted, allDepts };
    }, [data, getDepartment]);

    const DEPT_COLORS: Record<string, string> = {
        "DP": "#F59E0B",      // Amber (Amarelo)
        "Fiscal": "#3B82F6",  // Blue (Azul)
        "Contábil": "#16a34a", // Green-600 (Distinct Green)
        "Pessoal": "#F59E0B", // Alias for DP
        "Legal": "#8B5CF6",   // Violet
        "Societário": "#EC4899", // Pink
        "Financeiro": "#14B8A6", // Teal
        "Gerente": "#FFFFFF", // White
        "Gestão": "#FFFFFF",  // White
        "Não Definido": "#6B7280" // Gray
    };
    const FALLBACK_COLORS = ["#6366F1", "#F43F5E", "#84CC16", "#06B6D4"]; // Indigo, Rose, Lime, Cyan

    const getDeptColor = (dept: string, index: number) => {
        if (DEPT_COLORS[dept]) return DEPT_COLORS[dept];
        // Special case: match partial names if needed, e.g. "Depto Fiscal"
        if (dept.toLowerCase().includes("fiscal")) return DEPT_COLORS["Fiscal"];
        if (dept.toLowerCase().includes("contábil") || dept.toLowerCase().includes("contabil")) return DEPT_COLORS["Contábil"];
        if (dept.toLowerCase().includes("pessoal") || dept.toLowerCase().includes("dp")) return DEPT_COLORS["DP"];

        return FALLBACK_COLORS[index % FALLBACK_COLORS.length];
    };

    if (isLoading) {
        return (
            <Card className="col-span-1 lg:col-span-1">
                <CardHeader>
                    <CardTitle>Demanda por Cliente</CardTitle>
                </CardHeader>
                <CardContent className="h-[320px] flex items-center justify-center">
                    <div className="h-full w-full bg-gray-100 dark:bg-gray-800 animate-pulse rounded-lg" />
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="col-span-1 lg:col-span-1" style={{ background: 'var(--bg-card)' }}>
            <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between">
                    <span>Demanda por Cliente</span>
                    <div className="flex gap-2 text-[10px] font-normal">
                        {/* Mini Legend for Top Depts */}
                        {["DP", "Fiscal", "Contábil"].map(d => (
                            <span key={d} className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: DEPT_COLORS[d] }}></span>
                                {d}
                            </span>
                        ))}
                    </div>
                </CardTitle>
            </CardHeader>
            <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={chartData}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--chart-grid)" opacity={0.5} />
                        <XAxis type="number" hide />
                        <YAxis
                            dataKey="shortName"
                            type="category"
                            width={100}
                            tick={{ fontSize: 11, fill: "var(--chart-axis)" }}
                            interval={0}
                        />
                        <Tooltip
                            cursor={false}
                            contentStyle={{
                                backgroundColor: "var(--bg-card)",
                                borderColor: "var(--border-color)",
                                borderRadius: "8px",
                                color: "var(--text-primary)",
                                fontSize: "12px"
                            }}
                            formatter={(value: number | undefined, name: string | undefined) => [value ?? 0, (name === "total" ? "Total" : name) ?? ""]}
                            labelFormatter={(label, payload) => {
                                if (payload && payload.length > 0) return payload[0].payload.fullName;
                                return label;
                            }}
                            itemSorter={(item) => (item.value as number) * -1} // Sort tooltip descending
                        />
                        {allDepts.map((dept, index) => (
                            <Bar
                                key={dept}
                                dataKey={dept}
                                stackId="a"
                                fill={getDeptColor(dept, index)}
                                radius={[0, 0, 0, 0]}
                                barSize={20}
                            />
                        ))}
                        <Line
                            type="monotone"
                            dataKey="total"
                            stroke="none"
                            width={0}
                            dot={false}
                            activeDot={false}
                            isAnimationActive={false}
                        >
                            <LabelList
                                dataKey="total"
                                position="right"
                                style={{ fill: 'var(--text-primary)', fontSize: 11, fontWeight: 'bold' }}
                                offset={10}
                            />
                        </Line>
                    </ComposedChart>
                </ResponsiveContainer>
            </CardContent>

            {/* Full Ranking Expandable */}
            {fullRanking.length > 0 && (
                <div className="border-t border-gray-100 dark:border-gray-700/50">
                    <button
                        onClick={() => setShowFullRanking(!showFullRanking)}
                        className="w-full px-6 py-3 flex items-center justify-between text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                    >
                        <span>📋 Ranking Completo ({fullRanking.length} clientes)</span>
                        {showFullRanking ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                    {showFullRanking && (
                        <div className="max-h-[300px] overflow-auto px-6 pb-4">
                            <table className="w-full text-sm">
                                <thead className="text-xs text-gray-500 uppercase sticky top-0 bg-white dark:bg-[#282D33] z-10">
                                    <tr>
                                        <th className="text-left py-2">#</th>
                                        <th className="text-left py-2">Cliente</th>
                                        <th className="text-center py-2">Total</th>
                                        {allDepts.map(d => (
                                            <th key={d} className="text-center py-2" title={d}>
                                                <span
                                                    className="w-2 h-2 inline-block rounded-full mr-1"
                                                    style={{ backgroundColor: getDeptColor(d, 0) }}
                                                ></span>
                                                {d.substring(0, 3)}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {fullRanking.map((item: any, i: number) => (
                                        <tr key={i} className="border-t border-gray-100 dark:border-gray-700/30 hover:bg-gray-50 dark:hover:bg-gray-800/20">
                                            <td className="py-1.5 text-gray-400">{i + 1}</td>
                                            <td className="py-1.5 text-gray-900 dark:text-white font-medium truncate max-w-[150px]" title={item.name}>
                                                {item.name}
                                            </td>
                                            <td className="py-1.5 text-center font-bold text-gray-700 dark:text-gray-300">{item.total}</td>
                                            {allDepts.map(d => (
                                                <td key={d} className="py-1.5 text-center text-gray-500 dark:text-gray-400 font-mono text-xs">
                                                    {item[d] || "-"}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </Card>
    );
}
