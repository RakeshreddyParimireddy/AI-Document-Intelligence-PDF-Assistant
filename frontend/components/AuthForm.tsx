"use client";

// The shared form used by both the Login and Register pages.

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api";

type Mode = "login" | "register";

const TEXT = {
  login: {
    title: "Welcome back",
    subtitle: "Log in to chat with your documents",
    button: "Log in",
    busy: "Logging in…",
    switchText: "Don't have an account?",
    switchLink: { href: "/register", label: "Create one" },
  },
  register: {
    title: "Create your account",
    subtitle: "Upload PDFs and ask them questions",
    button: "Create account",
    busy: "Creating account…",
    switchText: "Already have an account?",
    switchLink: { href: "/login", label: "Log in" },
  },
};

export default function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const text = TEXT[mode];
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "register") await register(email, password);
      await login(email, password); // after registering, log straight in
      setPassword(""); // don't keep the password on screen after leaving this page
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 font-bold text-white">
            D
          </span>
          <span className="text-xl font-semibold text-slate-900">DocuMind</span>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm"
        >
          <div>
            <h1 className="text-xl font-semibold text-slate-900">{text.title}</h1>
            <p className="mt-1 text-sm text-slate-500">{text.subtitle}</p>
          </div>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              type="password"
              required
              minLength={mode === "register" ? 8 : undefined}
              maxLength={72}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
            {mode === "register" && (
              <span className="mt-1 block text-xs text-slate-400">At least 8 characters</span>
            )}
          </label>

          {error && (
            <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {busy ? text.busy : text.button}
          </button>

          <p className="text-center text-sm text-slate-500">
            {text.switchText}{" "}
            <Link href={text.switchLink.href} className="font-medium text-indigo-600 hover:underline">
              {text.switchLink.label}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
