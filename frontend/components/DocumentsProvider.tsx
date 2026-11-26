"use client";

// Keeps the user's document list in one place, shared by the sidebar and the dashboard.
// While any document is "processing", it re-checks the backend every 2 seconds,
// so the status changes to "ready" (or "failed") on screen by itself.

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
  type DocumentInfo,
} from "@/lib/api";

const POLL_INTERVAL_MS = 2000;

type DocumentsContextValue = {
  documents: DocumentInfo[];
  loading: boolean; // true until the first list has loaded
  error: string | null;
  refresh: () => Promise<void>;
  upload: (file: File) => Promise<void>;
  remove: (id: number) => Promise<void>;
};

const DocumentsContext = createContext<DocumentsContextValue | null>(null);

export function useDocuments(): DocumentsContextValue {
  const value = useContext(DocumentsContext);
  if (!value) throw new Error("useDocuments must be used inside <DocumentsProvider>");
  return value;
}

export default function DocumentsProvider({ children }: { children: React.ReactNode }) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await listDocuments());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  // Load the list when the app opens
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- loading data on mount
    refresh();
  }, [refresh]);

  // Poll while something is still processing
  const anyProcessing = documents.some((d) => d.status === "processing");
  useEffect(() => {
    if (!anyProcessing) return;
    const timer = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [anyProcessing, refresh]);

  const upload = useCallback(async (file: File) => {
    const doc = await uploadDocument(file);
    setDocuments((current) => [doc, ...current]); // show it right away as "processing"
  }, []);

  const remove = useCallback(async (id: number) => {
    await deleteDocument(id);
    setDocuments((current) => current.filter((d) => d.id !== id));
  }, []);

  return (
    <DocumentsContext.Provider value={{ documents, loading, error, refresh, upload, remove }}>
      {children}
    </DocumentsContext.Provider>
  );
}
