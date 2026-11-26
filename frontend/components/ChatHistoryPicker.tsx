"use client";

// The "chat history" dropdown and "+ New chat" button, used on both chat pages.

import type { Chat } from "@/lib/api";

export default function ChatHistoryPicker({
  chats,
  chatId,
  busy,
  onOpen,
}: {
  chats: Chat[];
  chatId: number | null;
  busy: boolean; // waiting for an answer: don't allow switching
  onOpen: (id: number | null) => void;
}) {
  return (
    <>
      <label className="sr-only" htmlFor="chat-history">
        Chat history
      </label>
      <select
        id="chat-history"
        value={chatId ?? ""}
        onChange={(e) => onOpen(e.target.value ? Number(e.target.value) : null)}
        disabled={busy}
        className="max-w-56 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
      >
        {chatId === null && <option value="">New chat</option>}
        {chats.map((chat) => (
          <option key={chat.id} value={chat.id}>
            {chat.title}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={() => onOpen(null)}
        disabled={chatId === null || busy}
        className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
      >
        + New chat
      </button>
    </>
  );
}
