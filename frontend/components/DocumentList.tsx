"use client";

import { useState } from "react";
import { useDocuments } from "@/components/DocumentsProvider";
import StatusBadge from "@/components/StatusBadge";
import type { DocumentInfo } from "@/lib/api";

function formatSize(sizeKb: number): string {
  return sizeKb >= 1024 ? `${(sizeKb / 1024).toFixed(1)} MB` : `${sizeKb} KB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function DocumentList() {
  const { documents, loading, error, remove } = useDocuments();
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function handleDelete(doc: DocumentInfo) {
    if (!window.confirm(`Delete "${doc.filename}"? This cannot be undone.`)) return;
    setDeletingId(doc.id);
    setDeleteError(null);
    try {
      await remove(doc.id);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Could not delete the document");
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) return <p className="py-6 text-sm text-slate-500">Loading documents…</p>;
  if (error) return <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>;
  if (documents.length === 0)
    return (
      <p className="rounded-2xl border border-slate-200 bg-white py-10 text-center text-sm text-slate-500">
        No documents yet. Upload a PDF to get started.
      </p>
    );

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      {deleteError && <p className="bg-red-50 px-4 py-2 text-sm text-red-700">{deleteError}</p>}
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-medium">Name</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Pages</th>
            <th className="px-4 py-3 font-medium">Size</th>
            <th className="px-4 py-3 font-medium">Uploaded</th>
            <th className="px-4 py-3">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {documents.map((doc) => (
            <tr key={doc.id} className="hover:bg-slate-50">
              <td className="max-w-xs truncate px-4 py-3 font-medium text-slate-800" title={doc.filename}>
                {doc.filename}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={doc.status} />
              </td>
              <td className="px-4 py-3 text-slate-600">{doc.status === "processing" ? "—" : doc.pages}</td>
              <td className="px-4 py-3 text-slate-600">{formatSize(doc.size_kb)}</td>
              <td className="px-4 py-3 text-slate-600">{formatDate(doc.uploaded_at)}</td>
              <td className="px-4 py-3 text-right">
                <button
                  type="button"
                  onClick={() => handleDelete(doc)}
                  disabled={deletingId === doc.id}
                  className="text-sm font-medium text-slate-400 hover:text-red-600 disabled:opacity-50"
                >
                  {deletingId === doc.id ? "Deleting…" : "Delete"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
