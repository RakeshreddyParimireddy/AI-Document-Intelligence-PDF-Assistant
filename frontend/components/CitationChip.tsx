"use client";

// A small clickable label under an answer, e.g. "invoice.pdf · p. 2".
// Clicking it shows the source text in the panel on the right.

export type SourceGroup = {
  documentId: number;
  document: string;
  page: number;
  snippets: string[];
};

export default function CitationChip({
  source,
  active,
  onClick,
}: {
  source: SourceGroup;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={`Show the source on page ${source.page}`}
      className={`inline-flex max-w-full items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset transition-colors ${
        active
          ? "bg-indigo-600 text-white ring-indigo-600"
          : "bg-indigo-50 text-indigo-700 ring-indigo-200 hover:bg-indigo-100"
      }`}
    >
      <span aria-hidden>📄</span>
      <span className="truncate">{source.document}</span>
      <span className="shrink-0">· p. {source.page}</span>
    </button>
  );
}
