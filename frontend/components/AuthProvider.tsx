"use client";

// Protects pages that need a logged-in user.
// It checks the saved token with the backend; if there is none (or it expired),
// it sends the user to /login. Pages inside can call useAuth() to get the user.

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, getMe, getToken, logout as clearToken, type User } from "@/lib/api";

type AuthContextValue = {
  user: User;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Runs every time this part of the app is shown (also after logging in again)
    let cancelled = false;
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    getMe()
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          clearToken(); // token expired or invalid
          router.replace("/login");
        } else {
          setError(err instanceof Error ? err.message : "Something went wrong");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  function logout() {
    clearToken();
    setUser(null);
    router.replace("/login");
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center p-6">
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  return <AuthContext.Provider value={{ user, logout }}>{children}</AuthContext.Provider>;
}
