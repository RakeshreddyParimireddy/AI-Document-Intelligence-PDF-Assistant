// All calls to the backend go through this file.
// Types here mirror backend/app/schemas.py.

// Remove a trailing "/" so "https://x.hf.space/" works too
const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const TOKEN_KEY = "documind_token";

// ---------- Types ----------
export type User = {
  id: number;
  email: string;
  created_at: string;
};

export type DocumentStatus = "processing" | "ready" | "failed";

export type DocumentInfo = {
  id: number;
  filename: string;
  pages: number;
  size_kb: number;
  status: DocumentStatus;
  uploaded_at: string;
};

export type DashboardStats = {
  documents: number;
  pages_processed: number;
  questions_asked: number;
};

export type Chat = {
  id: number;
  title: string;
  created_at: string;
  document_ids: number[];
};

export type Citation = {
  document_id: number;
  document: string; // filename
  page: number;
  snippet: string;
};

export type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
};

export type SummaryInfo = {
  document_id: number;
  summary: string;
  key_points: string[];
  created_at: string;
};

export type ExtractedField = {
  field: string;
  value: string | null; // null = not found in the document
  page: number | null;
};

export type ExtractResult = {
  document_id: number;
  results: ExtractedField[];
  note: string | null; // e.g. only part of a very long document was read
};

// Must match MAX_UPLOAD_MB on the backend (the backend checks too)
export const MAX_UPLOAD_MB = 20;
// Must match MAX_PDF_PAGES on the backend (only the backend can count pages, so it checks)
export const MAX_PDF_PAGES = 30;

// ---------- Errors ----------
export class ApiError extends Error {
  constructor(
    public status: number, // 0 = could not reach the server
    message: string,
  ) {
    super(message);
  }
}

// FastAPI errors look like {"detail": "text"} or {"detail": [{"msg": "text"}, ...]}
function readErrorDetail(data: unknown): string | undefined {
  const detail = (data as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg;
  return undefined;
}

// ---------- Login token (kept in the browser's localStorage) ----------
export function getToken(): string | null {
  if (typeof window === "undefined") return null; // not in a browser
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
}

// ---------- Shared request helper ----------
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Is the backend running?");
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      message = readErrorDetail(await response.json()) ?? message;
    } catch {
      // response had no JSON body; keep the default message
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) return undefined as T; // no content
  return response.json() as Promise<T>;
}

// ---------- Auth ----------
export function register(email: string, password: string): Promise<User> {
  return request<User>("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email: string, password: string): Promise<void> {
  // The backend expects form data with "username" (= email) and "password"
  const data = await request<{ access_token: string }>("/api/auth/login", {
    method: "POST",
    body: new URLSearchParams({ username: email, password }),
  });
  setToken(data.access_token);
}

export function getMe(): Promise<User> {
  return request<User>("/api/auth/me");
}

// ---------- Documents ----------
export function listDocuments(): Promise<DocumentInfo[]> {
  return request<DocumentInfo[]>("/api/documents");
}

export function uploadDocument(file: File): Promise<DocumentInfo> {
  const form = new FormData();
  form.append("file", file);
  // No Content-Type header: the browser sets it (with the file boundary) for FormData
  return request<DocumentInfo>("/api/documents/upload", { method: "POST", body: form });
}

export function deleteDocument(id: number): Promise<void> {
  return request<void>(`/api/documents/${id}`, { method: "DELETE" });
}

// ---------- Chat ----------
export function listChats(): Promise<Chat[]> {
  return request<Chat[]>("/api/chats");
}

export function createChat(documentIds: number[]): Promise<Chat> {
  return request<Chat>("/api/chats", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds }),
  });
}

export function listMessages(chatId: number): Promise<Message[]> {
  return request<Message[]>(`/api/chats/${chatId}/messages`);
}

// Returns the assistant's answer (the question is saved by the backend too)
export function askQuestion(chatId: number, question: string): Promise<Message> {
  return request<Message>(`/api/chats/${chatId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

// ---------- Insights: summary + extraction ----------
// The saved summary, or null if none has been made yet (free, no AI call)
export async function getSummary(documentId: number): Promise<SummaryInfo | null> {
  try {
    return await request<SummaryInfo>(`/api/documents/${documentId}/summary`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

// Makes a new summary with the AI (replaces the old one)
export function summarizeDocument(documentId: number): Promise<SummaryInfo> {
  return request<SummaryInfo>(`/api/documents/${documentId}/summarize`, { method: "POST" });
}

export function extractFields(documentId: number, fields: string[]): Promise<ExtractResult> {
  return request<ExtractResult>(`/api/documents/${documentId}/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fields }),
  });
}

// ---------- Dashboard ----------
export function getDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>("/api/dashboard/stats");
}
