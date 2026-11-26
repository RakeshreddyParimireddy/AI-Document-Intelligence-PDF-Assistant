"use client";

import { useAuth } from "@/components/AuthProvider";

// Dashboard. Upload box, document list and stats come in the next milestone.
export default function DashboardView() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-5xl p-8">
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-sm text-slate-500">Signed in as {user.email}</p>

      <div className="mt-8 rounded-2xl border-2 border-dashed border-slate-300 bg-white p-12 text-center">
        <p className="font-medium text-slate-700">Your documents will appear here</p>
        <p className="mt-1 text-sm text-slate-500">PDF upload is coming in the next step.</p>
      </div>
    </div>
  );
}
