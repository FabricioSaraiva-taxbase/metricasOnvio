"use client";

import { useState, useEffect, useCallback } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { UploadCloud, UserPlus, CheckCircle, AlertCircle, Tag, Database, Trash2, Save, Briefcase } from "lucide-react";

type TabKey = "upload" | "cliente" | "labels" | "base" | "departments";

interface MonthLabel {
    mes_key: string;
    label: string;
}

export default function ConfigPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState<TabKey>("upload");
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

    // Upload State
    const [file, setFile] = useState<File | null>(null);
    const [uploadNome, setUploadNome] = useState("");

    // Register Client State
    const [nomeContato, setNomeContato] = useState("");
    const [nomeCliente, setNomeCliente] = useState("");

    // Labels State
    const [labels, setLabels] = useState<Record<string, string>>({});
    const [months, setMonths] = useState<string[]>([]);
    const [selectedLabelMonth, setSelectedLabelMonth] = useState("");
    const [labelText, setLabelText] = useState("");

    // Global Base State
    const [baseFile, setBaseFile] = useState<File | null>(null);

    // Departments State
    const [auditAnalysts, setAuditAnalysts] = useState<string[]>([]);
    const [departmentMapping, setDepartmentMapping] = useState<Record<string, string>>({});
    const [deptLoading, setDeptLoading] = useState(false);

    // Load month labels
    const loadLabels = useCallback(async () => {
        try {
            const data = await api.get<{ labels?: Record<string, string> }>("/api/labels");
            setLabels(data.labels || {});
        } catch {
            // labels endpoint might not exist yet
        }
    }, []);



    // Load available months for labels
    const loadMonths = useCallback(async () => {
        try {
            const data = await api.get<{ data?: Record<string, any[]> }>("/api/data/list_months");
            const monthKeys: string[] = [];
            if (data.data) {
                Object.entries(data.data).forEach(([year, months]: [string, any]) => {
                    if (Array.isArray(months)) {
                        months.forEach((m: any) => {
                            const mesRaw = String(m.mes_raw || "").padStart(2, "0");
                            monthKeys.push(`${year}_${mesRaw}`);
                        });
                    }
                });
            }
            setMonths(monthKeys.sort().reverse());
            if (monthKeys.length > 0 && !selectedLabelMonth) {
                setSelectedLabelMonth(monthKeys[0]);
            }
        } catch {
            // ignore
        }
    }, [selectedLabelMonth]);

    useEffect(() => {
        if (activeTab === "labels") {
            loadLabels();
            loadMonths();
        }
    }, [activeTab, loadLabels, loadMonths]);

    // Update label text when month changes
    useEffect(() => {
        if (selectedLabelMonth && labels[selectedLabelMonth]) {
            setLabelText(labels[selectedLabelMonth]);
        } else {
            setLabelText("");
        }
    }, [selectedLabelMonth, labels]);

    // Load departments and analysts
    const loadDepartmentsData = useCallback(async () => {
        setDeptLoading(true);
        try {
            // 1. Fetch current mapping
            const mapRes = await api.get<Record<string, string>>("/api/departments");
            const upperMap: Record<string, string> = {};
            if (mapRes) {
                Object.entries(mapRes).forEach(([k, v]) => {
                    upperMap[k.toUpperCase()] = v;
                });
            }
            setDepartmentMapping(upperMap);

            // 2. Fetch ALL analysts from backend (scans all months)
            const analystsRes = await api.get<string[]>("/api/departments/analysts");

            const analystsSet = new Set<string>();
            // Add existing keys from mapping
            Object.keys(mapRes || {}).forEach(k => analystsSet.add(k.toUpperCase()));
            // Add analysts from data
            (analystsRes || []).forEach(a => analystsSet.add(a));

            setAuditAnalysts(Array.from(analystsSet).sort());

        } catch (error) {
            console.error("Error loading departments data", error);
        } finally {
            setDeptLoading(false);
        }
    }, []);

    useEffect(() => {
        if (activeTab === "departments") {
            loadDepartmentsData();
        }
    }, [activeTab, loadDepartmentsData]);

    const handleSaveDepartment = async (analyst: string, dept: string) => {
        try {
            await api.post("/api/departments", { analyst, department: dept });
            setDepartmentMapping(prev => ({ ...prev, [analyst]: dept }));
        } catch (error) {
            setMessage({ type: "error", text: "Erro ao salvar departamento." });
        }
    };

    if (user?.role !== "admin") {
        return (
            <DashboardLayout>
                <div className="flex flex-col items-center justify-center h-[60vh] text-center">
                    <AlertCircle className="h-16 w-16 text-red-500 mb-4" />
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Acesso Negado</h1>
                    <p className="text-gray-500 mt-2">Você não tem permissão para acessar esta página.</p>
                </div>
            </DashboardLayout>
        );
    }

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) {
            setMessage({ type: "error", text: "Selecione um arquivo CSV ou Excel." });
            return;
        }
        if (!uploadNome.trim()) {
            setMessage({ type: "error", text: "Informe o nome do mês (ex: 2026_03)." });
            return;
        }

        setIsLoading(true);
        setMessage(null);

        const formData = new FormData();
        formData.append("arquivo", file);
        formData.append("nome", uploadNome.trim());

        try {
            const res = await api.upload<{ message: string }>(
                "/api/admin/upload_month",
                formData
            );

            setMessage({ type: "success", text: res.message || "Arquivo enviado com sucesso!" });
            setFile(null);
            setUploadNome("");
        } catch (error) {
            setMessage({
                type: "error",
                text: error instanceof Error ? error.message : "Erro desconhecido.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleRegisterClient = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!nomeContato.trim() || !nomeCliente.trim()) {
            setMessage({ type: "error", text: "Preencha todos os campos." });
            return;
        }

        setIsLoading(true);
        setMessage(null);

        try {
            await api.post("/api/admin/register_client", {
                nome_contato: nomeContato,
                nome_cliente: nomeCliente,
            });

            setMessage({ type: "success", text: `Vínculo criado: ${nomeContato} → ${nomeCliente}` });
            setNomeContato("");
            setNomeCliente("");
        } catch (error) {
            setMessage({
                type: "error",
                text: error instanceof Error ? error.message : "Erro ao cadastrar cliente.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveLabel = async () => {
        if (!selectedLabelMonth) return;

        setIsLoading(true);
        setMessage(null);

        try {
            await api.put(`/api/labels/${selectedLabelMonth}`, { label: labelText });
            setMessage({ type: "success", text: `Label salvo para ${selectedLabelMonth}: "${labelText}"` });
            await loadLabels();
        } catch (error) {
            setMessage({
                type: "error",
                text: error instanceof Error ? error.message : "Erro ao salvar label.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleClearLabel = async () => {
        if (!selectedLabelMonth) return;

        setIsLoading(true);
        setMessage(null);

        try {
            await api.put(`/api/labels/${selectedLabelMonth}`, { label: "" });
            setLabelText("");
            setMessage({ type: "success", text: `Label removido de ${selectedLabelMonth}` });
            await loadLabels();
        } catch (error) {
            setMessage({
                type: "error",
                text: error instanceof Error ? error.message : "Erro ao remover label.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleUploadBase = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!baseFile) {
            setMessage({ type: "error", text: "Selecione o arquivo statusContatos.xlsx." });
            return;
        }

        setIsLoading(true);
        setMessage(null);

        const formData = new FormData();
        formData.append("file", baseFile);

        try {
            const res = await api.upload<{ message: string }>(
                "/api/admin/upload_base",
                formData
            );

            setMessage({ type: "success", text: res.message || "Base atualizada com sucesso!" });
            setBaseFile(null);
        } catch (error) {
            setMessage({
                type: "error",
                text: error instanceof Error ? error.message : "Erro desconhecido.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const tabs: { key: TabKey; label: string; icon: React.ReactNode }[] = [
        { key: "upload", label: "Upload de Mês", icon: <UploadCloud className="h-4 w-4" /> },
        { key: "cliente", label: "Cadastrar Cliente", icon: <UserPlus className="h-4 w-4" /> },
        { key: "labels", label: "Labels de Meses", icon: <Tag className="h-4 w-4" /> },
        { key: "base", label: "Atualizar Base", icon: <Database className="h-4 w-4" /> },
        { key: "departments", label: "Departamentos", icon: <Briefcase className="h-4 w-4" /> },
    ];

    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
                    Configurações
                </h1>

                {/* Tabs */}
                <div className="flex gap-4 mb-8 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
                    {tabs.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => {
                                setActiveTab(tab.key);
                                setMessage(null);
                            }}
                            className={`pb-4 px-2 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap ${activeTab === tab.key
                                ? "border-[#00A0E3] text-[#00A0E3]"
                                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                                }`}
                        >
                            {tab.icon}
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Feedback Message */}
                {message && (
                    <div
                        className={`p-4 mb-6 rounded-lg flex items-center gap-3 ${message.type === "success"
                            ? "bg-green-50 text-green-700 border border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800"
                            : "bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800"
                            }`}
                    >
                        {message.type === "success" ? (
                            <CheckCircle className="h-5 w-5 flex-shrink-0" />
                        ) : (
                            <AlertCircle className="h-5 w-5 flex-shrink-0" />
                        )}
                        <p className="text-sm font-medium">{message.text}</p>
                    </div>
                )}

                {/* Upload Tab */}
                {activeTab === "upload" && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Enviar Novo Mês</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleUpload} className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Nome do Mês (obrigatório)
                                    </label>
                                    <input
                                        type="text"
                                        value={uploadNome}
                                        onChange={(e) => setUploadNome(e.target.value)}
                                        placeholder="Ex: 2026_03"
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-[#00A0E3] focus:border-transparent bg-white dark:bg-[#1E2328] text-gray-900 dark:text-white"
                                    />
                                    <p className="mt-1 text-xs text-gray-500">Formato: ANO_MÊS (ex: 2026_03 para Março 2026)</p>
                                </div>

                                <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-12 text-center hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer relative">
                                    <input
                                        type="file"
                                        accept=".csv, .xlsx"
                                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    />
                                    <div className="flex flex-col items-center gap-2 pointer-events-none">
                                        <UploadCloud className="h-10 w-10 text-gray-400" />
                                        <p className="text-sm font-medium text-gray-900 dark:text-gray-200">
                                            {file ? file.name : "Clique para selecionar ou arraste aqui"}
                                        </p>
                                        <p className="text-xs text-gray-500">
                                            Suporta CSV (ponto e vírgula) ou Excel (.xlsx)
                                        </p>
                                    </div>
                                </div>

                                <div className="flex justify-end">
                                    <Button type="submit" disabled={!file || !uploadNome.trim()} isLoading={isLoading}>
                                        Enviar Arquivo
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                )}

                {/* Register Client Tab */}
                {activeTab === "cliente" && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Cadastrar De/Para (Contato → Cliente)</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleRegisterClient} className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                            Nome do Contato (no CSV)
                                        </label>
                                        <input
                                            type="text"
                                            value={nomeContato}
                                            onChange={(e) => setNomeContato(e.target.value.toUpperCase())}
                                            placeholder="Ex: MARIA SILVA"
                                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-[#00A0E3] focus:border-transparent bg-white dark:bg-[#1E2328] text-gray-900 dark:text-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                            Nome do Cliente (Correto)
                                        </label>
                                        <input
                                            type="text"
                                            value={nomeCliente}
                                            onChange={(e) => setNomeCliente(e.target.value.toUpperCase())}
                                            placeholder="Ex: PADARIA DO JOÃO"
                                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-[#00A0E3] focus:border-transparent bg-white dark:bg-[#1E2328] text-gray-900 dark:text-white"
                                        />
                                    </div>
                                </div>
                                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg text-sm text-blue-700 dark:text-blue-200">
                                    <p>
                                        Isso mapeará todas as ocorrências futuras de <strong>{nomeContato || "..."}</strong> para{" "}
                                        <strong>{nomeCliente || "..."}</strong>.
                                    </p>
                                </div>
                                <div className="flex justify-end">
                                    <Button type="submit" disabled={!nomeContato || !nomeCliente} isLoading={isLoading}>
                                        Cadastrar Vínculo
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                )}

                {/* Labels Tab */}
                {activeTab === "labels" && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Labels de Meses</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg text-sm text-amber-700 dark:text-amber-200">
                                    <p>Adicione um aviso visível na aba do mês (ex: <strong>PARCIAL - 09/02</strong>). Esse label aparece como badge no dashboard.</p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Selecionar Mês
                                    </label>
                                    <select
                                        value={selectedLabelMonth}
                                        onChange={(e) => setSelectedLabelMonth(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-[#00A0E3] focus:border-transparent bg-white dark:bg-[#1E2328] text-gray-900 dark:text-white"
                                    >
                                        {months.map((m) => (
                                            <option key={m} value={m}>
                                                {m.replace("_", "/")} {labels[m] ? `— ${labels[m]}` : ""}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Texto do Label
                                    </label>
                                    <input
                                        type="text"
                                        value={labelText}
                                        onChange={(e) => setLabelText(e.target.value)}
                                        placeholder="Ex: PARCIAL - 09/02"
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-[#00A0E3] focus:border-transparent bg-white dark:bg-[#1E2328] text-gray-900 dark:text-white"
                                    />
                                </div>

                                <div className="flex gap-3 justify-end">
                                    <Button
                                        variant="danger"
                                        onClick={handleClearLabel}
                                        disabled={!selectedLabelMonth || !labels[selectedLabelMonth]}
                                        isLoading={isLoading}
                                    >
                                        <Trash2 className="h-4 w-4 mr-2" />
                                        Limpar Label
                                    </Button>
                                    <Button
                                        onClick={handleSaveLabel}
                                        disabled={!selectedLabelMonth || !labelText.trim()}
                                        isLoading={isLoading}
                                    >
                                        <Save className="h-4 w-4 mr-2" />
                                        Salvar Label
                                    </Button>
                                </div>

                                {/* Existing labels preview */}
                                {Object.keys(labels).length > 0 && (
                                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Labels ativos:</h4>
                                        <div className="flex flex-wrap gap-2">
                                            {Object.entries(labels).map(([key, value]) => (
                                                <span
                                                    key={key}
                                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-sm"
                                                >
                                                    ⚠️ {key.replace("_", "/")}: {value}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Departments Tab */}
                {activeTab === "departments" && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Cadastro de Departamentos</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg text-sm text-blue-700 dark:text-blue-200">
                                    <p>Defina o departamento de cada analista. Sugestões são carregadas do mês mais recente.</p>
                                </div>

                                {deptLoading ? (
                                    <div className="text-center py-8 text-gray-500">Carregando analistas...</div>
                                ) : (
                                    <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2">
                                        {auditAnalysts.map((analyst) => (
                                            <div key={analyst} className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
                                                <span className="flex-1 font-medium text-sm text-gray-700 dark:text-gray-300">
                                                    {analyst}
                                                </span>
                                                <div className="w-1/2">
                                                    <input
                                                        type="text"
                                                        placeholder="Departamento (ex: Fiscal)"
                                                        value={departmentMapping[analyst] || ""}
                                                        onChange={(e) => setDepartmentMapping(prev => ({ ...prev, [analyst]: e.target.value }))}
                                                        onBlur={(e) => handleSaveDepartment(analyst, e.target.value)}
                                                        className="w-full px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-1 focus:ring-[#00A0E3] dark:bg-[#1E2328] dark:text-white"
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                        {auditAnalysts.length === 0 && (
                                            <p className="text-gray-500 text-center">Nenhum analista encontrado.</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Update Global Base Tab */}
                {activeTab === "base" && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Atualizar Base Global (statusContatos.xlsx)</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleUploadBase} className="space-y-6">
                                <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg text-sm text-amber-700 dark:text-amber-200">
                                    <p>
                                        <strong>⚠️ Atenção:</strong> Isso substituirá o arquivo <code className="bg-amber-100 dark:bg-amber-800/30 px-1 rounded">statusContatos.xlsx</code> que
                                        contém todos os mapeamentos De/Para. Faça backup antes.
                                    </p>
                                </div>

                                <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-12 text-center hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer relative">
                                    <input
                                        type="file"
                                        accept=".xlsx"
                                        onChange={(e) => setBaseFile(e.target.files?.[0] || null)}
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    />
                                    <div className="flex flex-col items-center gap-2 pointer-events-none">
                                        <Database className="h-10 w-10 text-gray-400" />
                                        <p className="text-sm font-medium text-gray-900 dark:text-gray-200">
                                            {baseFile ? baseFile.name : "Selecione statusContatos.xlsx"}
                                        </p>
                                        <p className="text-xs text-gray-500">
                                            Apenas arquivo Excel (.xlsx)
                                        </p>
                                    </div>
                                </div>

                                <div className="flex justify-end">
                                    <Button type="submit" disabled={!baseFile} isLoading={isLoading}>
                                        Salvar Base
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                )}
            </div>
        </DashboardLayout>
    );
}
