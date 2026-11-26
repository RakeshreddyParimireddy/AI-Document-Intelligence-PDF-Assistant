import type { DocumentStatus } from "@/lib/api";

const STYLES: Record<DocumentStatus, { label: string; className: string; title: string }> = {
  processing: {
    label: "Processing",
    className: "bg-amber-50 text-amber-700 ring-amber-200",
    title: "Reading the PDF and preparing it for questions",
  },
  ready: {
    label: "Ready",
    className: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    title: "Ready for questions",
  },
  failed: {
    label: "Failed",
    className: "bg-red-50 text-red-700 ring-red-200",
    title: "No readable text found (it may be a scanned PDF) or the file is damaged",
  },
};

export default function StatusBadge({ status }: { status: DocumentStatus }) {
  const style = STYLES[status];
  return (
    <span
      title={style.title}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style.className}`}
    >
      {status === "processing" && (
        <span className="h-2 w-2 animate-spin rounded-full border border-amber-600 border-t-transparent" />
      )}
      {style.label}
    </span>
  );
}
