"use client";

// One document's workspace with three tabs: Chat | Summary | Extract.
// On the Chat tab, the source panel on the right shows where an answer came from.

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import ChatWindow from "@/components/ChatWindow";
import type { SourceGroup } from "@/components/CitationChip";
import { useDocuments } from "@/components/DocumentsProvider";
import ExtractTable from "@/components/ExtractTable";
import SourcePanel from "@/components/SourcePanel";
import StatusBadge from "@/components/StatusBadge";
import SummaryCard from "@/components/SummaryCard";
import { askQuestion, createChat, listChats, listMessages, type Chat, type Message } from "@/lib/api";

const TABS = [
  { id: "chat", label: "Chat" },
  { id: "summary", label: "Summary" },
  { id: "extract", label: "Extract" },
] as const;
type Tab = (typeof TABS)[number]["id"];

function errorText(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback;
}

export default function DocumentWorkspace({ documentId }: { documentId: number }) {
  const { documents, loading: documentsLoading } = useDocuments();
  const doc = documents.find((d) => d.id === documentId);

  const [tab, setTab] = useState<Tab>("chat");
  const [chats, setChats] = useState<Chat[]>([]); // this document's chats, newest first
  const [chatId, setChatId] = useState<number | null>(null); // null = new, unsaved chat
  const [messages, setMessages] = useState<Message[]>([]);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<{ key: string; source: SourceGroup } | null>(null);
  // Chat we just created while asking: its messages are already on screen, don't reload them
  const justCreatedChatId = useRef<number | null>(null);

  // Chats that are about this one document (multi-document chats live elsewhere)
  const onlyThisDocument = useCallback(
    (all: Chat[]) =>
      all.filter((c) => c.document_ids.length === 1 && c.document_ids[0] === documentId),
    [documentId],
  );

  // Load chat history; open the newest chat if nothing is selected yet
  useEffect(() => {
    let cancelled = false;
    listChats()
      .then((all) => {
        if (cancelled) return;
        const mine = onlyThisDocument(all);
        setChats(mine);
        if (mine.length > 0) setChatId((current) => current ?? mine[0].id);
      })
      .catch((err) => {
        if (!cancelled) setError(errorText(err, "Could not load chats"));
      });
    return () => {
      cancelled = true;
    };
  }, [onlyThisDocument]);

  // Load the messages of the selected chat
  useEffect(() => {
    if (chatId === null || chatId === justCreatedChatId.current) return;
    let cancelled = false;
    listMessages(chatId)
      .then((list) => {
        if (!cancelled) setMessages(list);
      })
      .catch((err) => {
        if (!cancelled) setError(errorText(err, "Could not load messages"));
      });
    return () => {
      cancelled = true;
    };
  }, [chatId]);

  function openChat(id: number | null) {
    justCreatedChatId.current = null;
    setChatId(id);
    setMessages([]);
    setActiveSource(null);
    setError(null);
  }

  async function handleAsk(question: string): Promise<boolean> {
    setError(null);
    setThinking(true);
    // Show the question immediately (temporary negative id until the page reloads history)
    const pending: Message = {
      id: -Date.now(),
      role: "user",
      content: question,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, pending]);

    try {
      let id = chatId;
      if (id === null) {
        // First question: create the chat now
        id = (await createChat([documentId])).id;
        justCreatedChatId.current = id;
        setChatId(id);
      }
      const answer = await askQuestion(id, question);
      setMessages((current) => [...current, answer]);
      // Refresh the history list (a new chat gets its title from the first question)
      listChats()
        .then((all) => setChats(onlyThisDocument(all)))
        .catch(() => {});
      return true;
    } catch (err) {
      setMessages((current) => current.filter((m) => m.id !== pending.id));
      setError(errorText(err, "Could not get an answer"));
      return false;
    } finally {
      setThinking(false);
    }
  }

  if (!doc) {
    return documentsLoading ? (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
      </div>
    ) : (
      <div className="p-8">
        <p className="text-slate-700">Document not found.</p>
        <Link href="/" className="mt-2 inline-block text-sm font-medium text-indigo-600 hover:underline">
          ← Back to dashboard
        </Link>
      </div>
    );
  }

  const disabledReason =
    doc.status === "processing"
      ? "This document is still being processed…"
      : doc.status === "failed"
        ? "This document couldn't be read, so you can't ask about it."
        : null;

  return (
    <div className="flex h-full">
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header: document info, tabs, and (on the Chat tab) chat history */}
        <header className="border-b border-slate-200 bg-white px-6 pt-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="min-w-0 flex-1">
              <Link href="/" className="text-xs font-medium text-slate-400 hover:text-indigo-600">
                ← Dashboard
              </Link>
              <div className="mt-0.5 flex items-center gap-3">
                <h1 className="truncate text-lg font-semibold text-slate-900" title={doc.filename}>
                  {doc.filename}
                </h1>
                <StatusBadge status={doc.status} />
                {doc.status === "ready" && (
                  <span className="shrink-0 text-sm text-slate-400">{doc.pages} pages</span>
                )}
              </div>
            </div>

            {tab === "chat" && (
              <>
                <label className="sr-only" htmlFor="chat-history">
                  Chat history
                </label>
                <select
                  id="chat-history"
                  value={chatId ?? ""}
                  onChange={(e) => openChat(e.target.value ? Number(e.target.value) : null)}
                  disabled={thinking}
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
                  onClick={() => openChat(null)}
                  disabled={chatId === null || thinking}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  + New chat
                </button>
              </>
            )}
          </div>

          <nav className="mt-3 flex gap-6" role="tablist">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={tab === t.id}
                onClick={() => setTab(t.id)}
                className={`-mb-px border-b-2 pb-2.5 text-sm font-medium ${
                  tab === t.id
                    ? "border-indigo-600 text-indigo-700"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </header>

        {/* All tabs stay mounted (just hidden), so switching tabs keeps their content */}
        <div className={tab === "chat" ? "flex min-h-0 flex-1" : "hidden"}>
          <ChatWindow
            messages={messages}
            thinking={thinking}
            disabledReason={disabledReason}
            error={error}
            onAsk={handleAsk}
            activeSourceKey={activeSource?.key ?? null}
            onSelectSource={(key, source) => setActiveSource({ key, source })}
          />
        </div>
        <div className={tab === "summary" ? "flex-1 overflow-y-auto" : "hidden"}>
          <SummaryCard documentId={documentId} disabledReason={disabledReason} />
        </div>
        <div className={tab === "extract" ? "flex-1 overflow-y-auto" : "hidden"}>
          <ExtractTable
            documentId={documentId}
            filename={doc.filename}
            disabledReason={disabledReason}
          />
        </div>
      </div>

      {tab === "chat" && (
        <SourcePanel source={activeSource?.source ?? null} onClose={() => setActiveSource(null)} />
      )}
    </div>
  );
}
