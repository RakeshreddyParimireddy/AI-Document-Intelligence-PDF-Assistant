// All calls to the backend go through this file.
// Types here mirror backend/app/schemas.py.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "documind_token";

// ---------- Types ----------
export type User = {
  id: number;
  email: string;
  created_at: string;
};

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
