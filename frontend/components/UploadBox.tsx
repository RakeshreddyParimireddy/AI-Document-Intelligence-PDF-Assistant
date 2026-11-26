"use client";

// Drag & drop (or click to choose) PDF upload. Several files can be dropped at once;
// they are uploaded one after another.

import { useRef, useState } from "react";
import { MAX_UPLOAD_MB } from "@/lib/api";
import { useDocuments } from "@/components/DocumentsProvider";

// Returns an error message, or null if the file looks OK
function checkFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith(".pdf")) return `${file.name}: only PDF files are allowed`;
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024)
    return `${file.name}: too large (max ${MAX_UPLOAD_MB} MB)`;
  return null;
}

export default function UploadBox() {
  const { upload } = useDocuments();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState<string | null>(null); // name of the file being sent
  const [errors, setErrors] = useState<string[]>([]);

  async function handleFiles(fileList: FileList | null) {
    if (!fileList || uploading) return;
    const newErrors: string[] = [];
    for (const file of Array.from(fileList)) {
      const problem = checkFile(file);
      if (problem) {
        newErrors.push(problem);
        continue;
      }
      setUploading(file.name);
      try {
        await upload(file);
      } catch (err) {
        newErrors.push(`${file.name}: ${err instanceof Error ? err.message : "upload failed"}`);
      }
    }
    setUploading(null);
    setErrors(newErrors);
    if (inputRef.current) inputRef.current.value = ""; // allow choosing the same file again
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault(); // needed so the browser allows dropping here
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault(); // stop the browser from opening the PDF
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragging
            ? "border-indigo-500 bg-indigo-50"
            : "border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50"
        }`}
      >
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-xl text-indigo-600">
          ↑
        </div>
        {uploading ? (
          <p className="flex items-center gap-2 font-medium text-slate-700">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
            Uploading {uploading}…
          </p>
        ) : (
          <>
            <p className="font-medium text-slate-700">
              Drag & drop PDFs here, or <span className="text-indigo-600">browse</span>
            </p>
            <p className="mt-1 text-sm text-slate-500">PDF only, up to {MAX_UPLOAD_MB} MB each</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {errors.length > 0 && (
        <ul role="alert" className="mt-3 space-y-1 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {errors.map((message) => (
            <li key={message}>{message}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
