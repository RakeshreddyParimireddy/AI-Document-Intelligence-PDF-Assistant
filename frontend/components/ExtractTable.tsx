"use client";

// Extract tab: type the fields you want (e.g. "invoice date"), get a table, download it as CSV.

import { useState } from "react";
import { extractFields, type ExtractResult } from "@/lib/api";

const SUGGESTIONS = ["Invoice date", "Total amount", "Names", "Dates", "Key terms"];
const MAX_FIELDS = 20;

// Spreadsheet apps run cells starting with these characters as formulas.
// A malicious PDF could abuse that, so such values get a leading apostrophe.
function safeCell(value: string): string {
  const text = /^[=+\-@\t\r]/.test(value) ? `'${value}` : value;
  return `"${text.replaceAll('"', '""')}"`;
}

function downloadCsv(filename: string, result: ExtractResult) {
  const rows = [
    ["Field", "Value", "Page"],
    ...result.results.map((r) => [r.field, r.value ?? "", r.page ? String(r.page) : ""]),
  ];
  const csv = rows.map((row) => row.map(safeCell).join(",")).join("\r\n");
  // "﻿" makes Excel open the file as UTF-8 (so symbols like € show correctly)
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${filename.replace(/\.pdf$/i, "")}-extract.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function ExtractTable({
  documentId,
  filename,
  disabledReason,
}: {
  documentId: number;
  filename: string;
  disabledReason: string | null;
}) {
  const [fields, setFields] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addField(name: string) {
    const field = name.trim();
    if (!field || field.length > 100 || fields.length >= MAX_FIELDS) return;
    if (fields.some((f) => f.toLowerCase() === field.toLowerCase())) return; // already added
    setFields([...fields, field]);
    setDraft("");
  }

  async function extract() {
    setExtracting(true);
    setError(null);
    try {
      setResult(await extractFields(documentId, fields));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not extract the fields");
    } finally {
      setExtracting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      {/* Field picker */}
      <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Extract information</h2>
          <p className="text-sm text-slate-500">
            Add the fields you want to find, then click Extract.
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            addField(draft);
          }}
          className="flex gap-2"
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            maxLength={100}
            placeholder="e.g. Invoice date (press Enter to add)"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
          />
          <button
            type="submit"
            disabled={!draft.trim() || fields.length >= MAX_FIELDS}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Add
          </button>
        </form>

        {/* Quick suggestions */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400">Suggestions:</span>
          {SUGGESTIONS.filter((s) => !fields.some((f) => f.toLowerCase() === s.toLowerCase())).map(
            (s) => (
              <button
                key={s}
                type="button"
                onClick={() => addField(s)}
                className="rounded-full border border-dashed border-slate-300 px-2.5 py-0.5 text-xs text-slate-600 hover:border-indigo-400 hover:text-indigo-600"
              >
                + {s}
              </button>
            ),
          )}
        </div>

        {/* Chosen fields */}
        {fields.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {fields.map((field) => (
              <span
                key={field}
                className="inline-flex items-center gap-1 rounded-full bg-indigo-50 py-1 pl-3 pr-1.5 text-sm text-indigo-700 ring-1 ring-inset ring-indigo-200"
              >
                {field}
                <button
                  type="button"
                  onClick={() => setFields(fields.filter((f) => f !== field))}
                  aria-label={`Remove ${field}`}
                  className="rounded-full px-1.5 text-indigo-400 hover:bg-indigo-100 hover:text-indigo-700"
                >
                  ✕
                </button>
              </span>
            ))}
          </div>
        )}

        <button
          type="button"
          onClick={extract}
          disabled={fields.length === 0 || extracting || Boolean(disabledReason)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {extracting ? "Extracting… (can take up to a minute)" : "Extract"}
        </button>
        {disabledReason && <p className="text-sm text-slate-500">{disabledReason}</p>}
        {error && (
          <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        )}
      </section>

      {/* Results */}
      {result && (
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
            <h3 className="text-sm font-semibold text-slate-900">Results</h3>
            <button
              type="button"
              onClick={() => downloadCsv(filename, result)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              ⬇ Download CSV
            </button>
          </div>
          {result.note && <p className="bg-amber-50 px-5 py-2 text-sm text-amber-800">{result.note}</p>}
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-2.5 font-medium">Field</th>
                <th className="px-5 py-2.5 font-medium">Value</th>
                <th className="px-5 py-2.5 font-medium">Page</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {result.results.map((row) => (
                <tr key={row.field}>
                  <td className="px-5 py-3 font-medium text-slate-800">{row.field}</td>
                  <td className="whitespace-pre-wrap px-5 py-3 text-slate-700">
                    {row.value ?? <span className="italic text-slate-400">Not found</span>}
                  </td>
                  <td className="px-5 py-3 text-slate-500">{row.page ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
