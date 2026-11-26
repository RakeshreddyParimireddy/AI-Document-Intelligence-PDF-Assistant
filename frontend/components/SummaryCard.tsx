"use client";

// Summary tab: shows the saved summary, or a button to make one with the AI.

import { useEffect, useState } from "react";
import { getSummary, summarizeDocument, type SummaryInfo } from "@/lib/api";

export default function SummaryCard({
  documentId,
  disabledReason,
}: {
  documentId: number;
  disabledReason: string | null; // e.g. the document is still processing
}) {
  const [summary, setSummary] = useState<SummaryInfo | null>(null);
  const [loaded, setLoaded] = useState(false); // finished checking for a saved summary
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load a saved summary, if there is one
  useEffect(() => {
    let cancelled = false;
    getSummary(documentId)
      .then((saved) => {
        if (!cancelled) setSummary(saved);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load the summary");
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [documentId]);

  async function generate() {
    setGenerating(true);
    setError(null);
    try {
      setSummary(await summarizeDocument(documentId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the summary");
    } finally {
      setGenerating(false);
    }
  }

  const button = (
    <button
      type="button"
      onClick={generate}
      disabled={generating || Boolean(disabledReason)}
      className={
        summary
          ? "rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          : "rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      }
    >
      {generating ? "Summarizing…" : summary ? "↻ Regenerate" : "Generate summary"}
    </button>
  );

  return (
    <div className="mx-auto max-w-3xl space-y-4 p-6">
      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!loaded ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : generating && !summary ? (
        <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
          Reading the whole document… this can take up to a minute.
        </div>
      ) : summary ? (
        <article className="space-y-6 rounded-2xl border border-slate-200 bg-white p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Summary</h2>
              <p className="text-xs text-slate-400">
                Made {new Date(summary.created_at).toLocaleString()}
              </p>
            </div>
            {button}
          </div>
          <p className="whitespace-pre-wrap leading-relaxed text-slate-700">{summary.summary}</p>
          {summary.key_points.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Key points
              </h3>
              <ul className="space-y-2">
                {summary.key_points.map((point, i) => (
                  <li key={i} className="flex gap-3 text-sm text-slate-700">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-500" />
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </article>
      ) : (
        <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-10 text-center">
          <p className="font-medium text-slate-800">No summary yet</p>
          <p className="mb-4 mt-1 text-sm text-slate-500">
            {disabledReason ?? "Get a short summary and the key points of this document."}
          </p>
          {button}
        </div>
      )}
    </div>
  );
}
