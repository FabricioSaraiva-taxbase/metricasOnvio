"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface MonthLabelBadgeProps {
    year: number;
    month: number;
}

export function MonthLabelBadge({ year, month }: MonthLabelBadgeProps) {
    const [label, setLabel] = useState<string | null>(null);

    useEffect(() => {
        const fetchLabels = async () => {
            try {
                const data = await api.get<{ labels?: Record<string, string> }>("/api/labels");
                const mesKey = `${year}_${String(month).padStart(2, "0")}`;
                const labels = data.labels || {};
                if (labels[mesKey]) {
                    setLabel(labels[mesKey]);
                } else {
                    setLabel(null);
                }
            } catch {
                setLabel(null);
            }
        };

        if (year && month) {
            fetchLabels();
        }
    }, [year, month]);

    if (!label) return null;

    return (
        <div
            className="w-full text-center py-2.5 px-4 rounded-xl font-bold text-sm text-white shadow-md"
            style={{
                background: "linear-gradient(135deg, #FFA726, #FB8C00)",
                boxShadow: "0 2px 8px rgba(251, 140, 0, 0.3)",
            }}
        >
            ⚠️ {label}
        </div>
    );
}
