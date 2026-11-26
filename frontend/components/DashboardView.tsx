"use client";

import { useAuth } from "@/components/AuthProvider";
import DocumentList from "@/components/DocumentList";
import StatsCards from "@/components/StatsCards";
import UploadBox from "@/components/UploadBox";

export default function DashboardView() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">Signed in as {user.email}</p>
      </div>

      <StatsCards />
      <UploadBox />

      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-900">Your documents</h2>
        <DocumentList />
      </section>
    </div>
  );
}
