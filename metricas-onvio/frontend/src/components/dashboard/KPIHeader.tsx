import { Card, CardContent } from "@/components/ui/Card";
import { Users, FileText, CheckCircle, Building } from "lucide-react";

interface KPIItem {
    label: string;
    value: string;
    icon: string;
}

interface KPIHeaderProps {
    kpis: KPIItem[];
    isLoading?: boolean;
}

const iconMap: Record<string, typeof FileText> = {
    "📊": FileText,
    "✅": CheckCircle,
    "🏢": Users,
    "🔄": Building,
};

const colorMap: Record<string, { color: string; bg: string }> = {
    "📊": { color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-500/10" },
    "✅": { color: "text-green-500", bg: "bg-green-50 dark:bg-green-500/10" },
    "🏢": { color: "text-purple-500", bg: "bg-purple-50 dark:bg-purple-500/10" },
    "🔄": { color: "text-gray-500", bg: "bg-gray-50 dark:bg-gray-500/10" },
};

export function KPIHeader({ kpis, isLoading }: KPIHeaderProps) {
    if (isLoading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(3)].map((_, i) => (
                    <Card key={i} className="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 border-none" />
                ))}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {kpis.map((kpi, index) => {
                const IconComponent = iconMap[kpi.icon] || FileText;
                const colors = colorMap[kpi.icon] || { color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-500/10" };

                return (
                    <Card key={index} className="hover:shadow-md transition-shadow">
                        <CardContent className="flex items-center gap-4 p-6">
                            <div className={`p-3 rounded-full ${colors.bg}`}>
                                <IconComponent className={`h-6 w-6 ${colors.color}`} />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                                    {kpi.label}
                                </p>
                                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                                    {kpi.value}
                                </h3>
                            </div>
                        </CardContent>
                    </Card>
                );
            })}
        </div>
    );
}
