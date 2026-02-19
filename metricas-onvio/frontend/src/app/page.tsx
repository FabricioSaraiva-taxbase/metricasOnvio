"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { FilterBar } from "@/components/dashboard/FilterBar";
import { KPIHeader } from "@/components/dashboard/KPIHeader";
import { EvolutionChart } from "@/components/dashboard/EvolutionChart";
import { TopClientsChart } from "@/components/dashboard/TopClientsChart";
import { QuickRegister } from "@/components/dashboard/QuickRegister";
import { MonthLabelBadge } from "@/components/dashboard/MonthLabelBadge";
import { useFilter } from "@/contexts/FilterContext";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Download, Search, Loader2, ArrowUpDown } from "lucide-react";

// Helper: parse date string and extract date/time parts
function parseDateTimeFromRecord(item: any): { dateStr: string; timeStr: string } {
  const raw = item.Data || "";
  let dateStr = raw;
  let timeStr = item.Hora || "";

  // Always clean dateStr if it has time components
  if (dateStr.includes("T")) {
    const parts = dateStr.split("T");
    dateStr = parts[0];
    // Only populate time if missing
    if (!timeStr) timeStr = parts[1]?.substring(0, 5) || "";
  } else if (dateStr.includes(" ")) {
    const parts = dateStr.split(" ");
    dateStr = parts[0];
    if (!timeStr) timeStr = parts[1]?.substring(0, 5) || "";
  }

  // Format date as dd/MM/yyyy if it's yyyy-MM-dd
  // Be strict about matching pure date string to avoid partial matches
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const [y, m, d] = dateStr.split("-");
    dateStr = `${d}/${m}/${y}`;
  }

  return { dateStr, timeStr };
}

// Helper: extract raw date (yyyy-MM-dd) from record for filtering/sorting
function getRawDate(item: any): string {
  const raw = item.Data || "";
  if (raw.includes("T")) return raw.split("T")[0];
  if (raw.includes(" ")) return raw.split(" ")[0];
  // If already dd/MM/yyyy, convert back
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) {
    const [d, m, y] = raw.split("/");
    return `${y}-${m}-${d}`;
  }
  return raw;
}

export default function DashboardPage() {
  const {
    selectedYear,
    selectedMonth,
    selectedAnalyst,
    selectedClient,
    selectedDepartment,
    getDepartment,
    refreshKey,
    refreshData,
    periodMode,
    customStartDate,
    customEndDate,
    allMonthIds,
    availableMonths,
  } = useFilter();

  const [rawData, setRawData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // ... (existing search state) ...
  const [searchTerm, setSearchTerm] = useState("");
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: "asc" | "desc";
  } | null>(null);

  // ... (existing data fetching logic) ... 
  // (Keep monthIdsToFetch and useEffect as is, skipping re-implementation in block for brevity unless needed)

  // Determine which month IDs to fetch
  const monthIdsToFetch = useMemo(() => {
    if (periodMode === "month") {
      return selectedMonth ? [selectedMonth] : [];
    }
    // For multi-month modes, use all available month IDs
    return allMonthIds;
  }, [periodMode, selectedMonth, allMonthIds]);

  // Fetch data (single or multiple months)
  useEffect(() => {
    if (monthIdsToFetch.length === 0) return;

    const fetchData = async () => {
      setIsLoading(true);
      try {
        if (monthIdsToFetch.length === 1) {
          // Single month fetch
          const data = await api.get<{
            records?: any[];
            registros?: any[];
            data?: any[];
          }>(`/api/data/get_month/${encodeURIComponent(monthIdsToFetch[0])}`);
          setRawData(data.records || data.registros || data.data || []);
        } else {
          // Multi-month: optimized fetch
          const data = await api.getPeriod<{
            records?: any[];
            registros?: any[];
            data?: any[];
          }>(monthIdsToFetch);
          setRawData(data.records || data.registros || data.data || []);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
        setRawData([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [monthIdsToFetch, refreshKey]);

  // Filter by date range when in multi-month mode
  const dateFilteredData = useMemo(() => {
    if (periodMode === "month") return rawData;

    const now = new Date();
    let startDate: Date | null = null;
    let endDate: Date | null = null;

    if (periodMode === "90d") {
      startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
    } else if (periodMode === "180d") {
      startDate = new Date(now.getTime() - 180 * 24 * 60 * 60 * 1000);
    } else if (periodMode === "custom") {
      if (customStartDate) startDate = new Date(customStartDate + "T00:00:00");
      if (customEndDate) endDate = new Date(customEndDate + "T23:59:59");
    }
    // "all" mode: no date filter

    if (!startDate && !endDate) return rawData;

    return rawData.filter((item) => {
      const rawDate = getRawDate(item);
      if (!rawDate) return true;
      const itemDate = new Date(rawDate + "T12:00:00");
      if (startDate && itemDate < startDate) return false;
      if (endDate && itemDate > endDate) return false;
      return true;
    });
  }, [rawData, periodMode, customStartDate, customEndDate]);

  // Apply analyst, client & DEPARTMENT filters
  const filteredData = useMemo(() => {
    let result = dateFilteredData;

    if (selectedAnalyst && selectedAnalyst !== "Todos") {
      result = result.filter(
        (item) => item["Atendido por"] === selectedAnalyst
      );
    }

    if (selectedClient && selectedClient !== "Todos (Visão Geral)") {
      result = result.filter(
        (item) => item.Cliente_Final === selectedClient
      );
    }

    if (selectedDepartment && selectedDepartment !== "Todos") {
      result = result.filter(
        (item) => getDepartment(item["Atendido por"]) === selectedDepartment
      );
    }

    return result;
  }, [dateFilteredData, selectedAnalyst, selectedClient, selectedDepartment, getDepartment]);

  // ... (kpis, validData logic unchanged) ...
  const EXCLUDED = ["TAXBASE INTERNO", "IGNORAR", "NÃO IDENTIFICADO"];
  const validData = useMemo(() => {
    return filteredData.filter(
      (item) => !EXCLUDED.includes(item.Cliente_Final || "")
    );
  }, [filteredData]);

  // KPIs
  const kpis = useMemo(() => {
    const totalBruto = filteredData.length;
    const totalValidos = validData.length;
    const clientesUnicos = new Set(
      validData.map((item) => item.Cliente_Final)
    ).size;

    return [
      {
        label: "Total Geral",
        value: totalBruto.toLocaleString("pt-BR"),
        icon: "📊",
      },
      {
        label: "Atendimentos Válidos",
        value: totalValidos.toLocaleString("pt-BR"),
        icon: "✅",
      },
      {
        label: "Clientes Únicos",
        value: clientesUnicos.toLocaleString("pt-BR"),
        icon: "🏢",
      },
    ];
  }, [filteredData, validData]);

  // ... (chart logic unchanged) ...
  const yearNum = selectedYear
    ? parseInt(selectedYear)
    : new Date().getFullYear();
  const monthNum = useMemo(() => {
    if (!selectedMonth) return new Date().getMonth() + 1;
    const bqMatch = selectedMonth.match(/(\d{4})_(\d{2})/);
    if (bqMatch) return parseInt(bqMatch[2]);
    return new Date().getMonth() + 1;
  }, [selectedMonth]);

  // ... (sort handleSort unchanged) ...
  const handleSort = useCallback(
    (key: string) => {
      let direction: "asc" | "desc" = "asc";
      if (
        sortConfig &&
        sortConfig.key === key &&
        sortConfig.direction === "asc"
      ) {
        direction = "desc";
      }
      setSortConfig({ key, direction });
    },
    [sortConfig]
  );


  const analysisData = useMemo(() => {
    let activeData = [...filteredData];

    // Search filter
    if (searchTerm) {
      const lowerTerm = searchTerm.toLowerCase();
      activeData = activeData.filter((item) =>
        Object.values(item).some((val) =>
          String(val).toLowerCase().includes(lowerTerm)
        )
      );
    }

    // Sort
    if (sortConfig) {
      activeData.sort((a, b) => {
        const aVal = a[sortConfig.key] || "";
        const bVal = b[sortConfig.key] || "";
        // Special handling for computed columns
        if (sortConfig.key === "Department") {
          const deptA = getDepartment(a["Atendido por"]);
          const deptB = getDepartment(b["Atendido por"]);
          if (deptA < deptB) return sortConfig.direction === "asc" ? -1 : 1;
          if (deptA > deptB) return sortConfig.direction === "asc" ? 1 : -1;
          return 0;
        }

        if (aVal < bVal) return sortConfig.direction === "asc" ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === "asc" ? 1 : -1;
        return 0;
      });
    } else {
      // Default sort by Date desc
      activeData.sort((a, b) => {
        const dateA = a.Data || "";
        const dateB = b.Data || "";
        return dateB.localeCompare(dateA);
      });
    }

    return activeData;
  }, [filteredData, searchTerm, sortConfig, getDepartment]);

  // Download CSV
  const handleDownload = async () => {
    try {
      // Always generate CSV client-side to ensure consistent encoding and columns
      const headers = ["Data", "Hora", "Analista", "Departamento", "Contato", "Cliente_Final", "Status"];
      const csvRows = [headers.join(";")];
      analysisData.forEach((item) => {
        const { dateStr, timeStr } = parseDateTimeFromRecord(item);
        const isInternal =
          item.Cliente_Final === "TAXBASE INTERNO" ||
          item.Cliente_Final === "IGNORAR";
        const isUnknown = item.Cliente_Final === "NÃO IDENTIFICADO";
        const status = isInternal
          ? "Interno/Ignorar"
          : isUnknown
            ? "Não Identificado"
            : "Válido";

        const analyst = (item["Atendido por"] || "").toUpperCase();
        const dept = getDepartment(analyst);

        csvRows.push(
          [
            dateStr,
            timeStr,
            analyst,
            dept,
            item.Contato || "",
            item.Cliente_Final || item.CLIENTE || "",
            status,
          ].join(";")
        );
      });
      const csvContent = "\uFEFF" + csvRows.join("\n"); // Add BOM
      const blob = new Blob([csvContent], {
        type: "text/csv;charset=utf-8;",
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const filename = periodMode === "month" && selectedMonth
        ? `relatorio_${selectedMonth}.csv`
        : `relatorio_${periodMode}_${new Date().toISOString().split("T")[0]}.csv`;

      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Erro ao baixar o relatório. Tente novamente.");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Filter Bar */}
        <FilterBar data={dateFilteredData} />

        {/* ... (Badge, QuickRegister, KPIHeader, Charts -- unchanged) ... */}
        {periodMode === "month" && (
          <MonthLabelBadge year={yearNum} month={monthNum} />
        )}
        <QuickRegister data={dateFilteredData} onRegistered={refreshData} />
        <KPIHeader kpis={kpis} isLoading={isLoading} />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <EvolutionChart
            data={validData}
            year={yearNum}
            month={monthNum}
            isLoading={isLoading}
          />
          <TopClientsChart data={filteredData} isLoading={isLoading} />
        </div>

        {/* ========== ANÁLISE DETALHADA ========== */}
        <Card className="overflow-hidden flex flex-col">
          <CardHeader className="flex flex-row items-center justify-between">
            {/* ... (Header unchanged) ... */}
            <div className="flex items-center gap-4">
              <CardTitle>
                Análise Detalhada ({analysisData.length})
              </CardTitle>
              <Button
                onClick={handleDownload}
                disabled={isLoading}
                className="gap-2"
              >
                <Download className="h-4 w-4" />
                Baixar CSV
              </Button>
            </div>
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Buscar..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-[#00A0E3]"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0 overflow-auto max-h-[600px]">
            {isLoading ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : analysisData.length === 0 ? (
              <div className="p-12 text-center text-gray-500">
                Nenhum registro encontrado.
              </div>
            ) : (
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-800/50 dark:text-gray-400 sticky top-0">
                  <tr>
                    <th
                      scope="col"
                      className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => handleSort("Data")}
                    >
                      <div className="flex items-center gap-1">
                        Data{" "}
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => handleSort("Hora")}
                    >
                      <div className="flex items-center gap-1">
                        Hora{" "}
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => handleSort("Atendido por")}
                    >
                      <div className="flex items-center gap-1">
                        Analista{" "}
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => handleSort("Department")}
                    >
                      <div className="flex items-center gap-1">
                        Departamento{" "}
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => handleSort("Contato")}
                    >
                      <div className="flex items-center gap-1">
                        Contato{" "}
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-6 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() =>
                        handleSort("Cliente_Final")
                      }
                    >
                      <div className="flex items-center gap-1">
                        Cliente Final{" "}
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th scope="col" className="px-6 py-3">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {analysisData.map((item, index) => {
                    const isInternal =
                      item.Cliente_Final ===
                      "TAXBASE INTERNO" ||
                      item.Cliente_Final === "IGNORAR";
                    const isUnknown =
                      item.Cliente_Final ===
                      "NÃO IDENTIFICADO";
                    const { dateStr, timeStr } =
                      parseDateTimeFromRecord(item);

                    const analyst = (item["Atendido por"] || "-").toUpperCase();
                    const dept = getDepartment(analyst);

                    return (
                      <tr
                        key={index}
                        className="bg-white border-b dark:bg-[#282D33] dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                      >
                        <td className="px-6 py-4 font-medium text-gray-900 dark:text-white whitespace-nowrap">
                          {dateStr}
                        </td>
                        <td className="px-6 py-4">
                          {timeStr || "-"}
                        </td>
                        <td className="px-6 py-4 text-gray-600 dark:text-gray-300">
                          {analyst}
                        </td>
                        <td className="px-6 py-4 text-gray-600 dark:text-gray-300">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                            {dept}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {item.Contato}
                        </td>
                        <td className="px-6 py-4 font-semibold">
                          {item.Cliente_Final ||
                            item.CLIENTE ||
                            "-"}
                        </td>
                        <td className="px-6 py-4">
                          {isInternal ? (
                            <span className="px-2 py-1 text-xs font-semibold text-gray-600 bg-gray-100 rounded-full dark:bg-gray-700 dark:text-gray-300">
                              Interno/Ignorar
                            </span>
                          ) : isUnknown ? (
                            <span className="px-2 py-1 text-xs font-semibold text-yellow-700 bg-yellow-100 rounded-full dark:bg-yellow-900/30 dark:text-yellow-400">
                              Não Identificado
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs font-semibold text-green-700 bg-green-100 rounded-full dark:bg-green-900/30 dark:text-green-400">
                              Válido
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
