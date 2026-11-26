"use client";

import { useEffect, useState } from "react";
import { useDocuments } from "@/components/DocumentsProvider";
import { getDashboardStats, type DashboardStats } from "@/lib/api";

export default function StatsCards() {
  const { documents } = useDocuments();
  const [stats, setStats] = useState<DashboardStats | null>(null);

  // Reload the numbers whenever the documents change (upload, delete, status change)
  const documentsKey = documents.map((d) => `${d.id}:${d.status}`).join(",");
  useEffect(() => {
    let cancelled = false;
    getDashboardStats()
      .then((data) => {
        if (!cancelled) setStats(data);
      })
      .catch(() => {
        // Stats are nice-to-have; keep showing the old numbers if this fails
      });
    return () => {
      cancelled = true;
    };
  }, [documentsKey]);

  const cards = [
    { label: "Documents", value: stats?.documents },
    { label: "Pages processed", value: stats?.pages_processed },
    { label: "Questions asked", value: stats?.questions_asked },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {cards.map((card) => (
        <div key={card.label} className="rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">{card.label}</p>
          <p className="mt-1 text-3xl font-semibold text-slate-900">{card.value ?? "–"}</p>
        </div>
      ))}
    </div>
  );
}
