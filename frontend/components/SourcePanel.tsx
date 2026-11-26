"use client";

// Right-hand panel: shows the text an answer was based on.

import type { SourceGroup } from "@/components/CitationChip";

export default function SourcePanel({
  source,
  onClose,
}: {
  source: SourceGroup | null;
  onClose: () => void;
}) {
  return (
    <aside className="hidden w-80 shrink-0 flex-col border-l border-slate-200 bg-white lg:flex">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-900">Source</h2>
        {source && (
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-slate-400 hover:text-slate-700"
            aria-label="Close source"
          >
            ✕
          </button>
        )}
      </div>

      {source ? (
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          <div>
            <p className="truncate text-sm font-medium text-slate-900" title={source.document}>
              {source.document}
            </p>
            <p className="text-xs text-slate-500">Page {source.page}</p>
          </div>
          {source.snippets.map((snippet, i) => (
            <blockquote
              key={i}
              className="rounded-lg border-l-4 border-indigo-400 bg-indigo-50/50 px-4 py-3 text-sm leading-relaxed text-slate-700"
            >
              {snippet}
              {snippet.length >= 300 && "…"}
            </blockquote>
          ))}
        </div>
      ) : (
        <p className="p-5 text-sm text-slate-500">
          Click a citation under an answer to see the text it came from.
        </p>
      )}
    </aside>
  );
}
