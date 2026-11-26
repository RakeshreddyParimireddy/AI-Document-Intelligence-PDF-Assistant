"use client";

// One document's workspace with three tabs: Chat | Summary | Extract.
// On the Chat tab, the source panel on the right shows where an answer came from.

import { useCallback, useState } from "react";
import Link from "next/link";
import ChatHistoryPicker from "@/components/ChatHistoryPicker";
import ChatWindow from "@/components/ChatWindow";
import { useDocuments } from "@/components/DocumentsProvider";
import ExtractTable from "@/components/ExtractTable";
import SourcePanel from "@/components/SourcePanel";
import StatusBadge from "@/components/StatusBadge";
import SummaryCard from "@/components/SummaryCard";
import type { Chat } from "@/lib/api";
import { useChatSession } from "@/lib/useChatSession";

const TABS = [
  { id: "chat", label: "Chat" },
  { id: "summary", label: "Summary" },
  { id: "extract", label: "Extract" },
] as const;
type Tab = (typeof TABS)[number]["id"];

export default function DocumentWorkspace({ documentId }: { documentId: number }) {
  const { documents, loading: documentsLoading } = useDocuments();
  const doc = documents.find((d) => d.id === documentId);
  const [tab, setTab] = useState<Tab>("chat");

  // Only chats about this one document (multi-document chats live on /chats)
  const belongsHere = useCallback(
    (chat: Chat) => chat.document_ids.length === 1 && chat.document_ids[0] === documentId,
    [documentId],
  );
  const session = useChatSession({ belongsHere, documentIdsForNewChat: [documentId] });

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
              <ChatHistoryPicker
                chats={session.chats}
                chatId={session.chatId}
                busy={session.thinking}
                onOpen={session.openChat}
              />
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
            messages={session.messages}
            thinking={session.thinking}
            disabledReason={disabledReason}
            error={session.error}
            onAsk={session.ask}
            activeSourceKey={session.activeSource?.key ?? null}
            onSelectSource={(key, source) => session.setActiveSource({ key, source })}
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
        <SourcePanel
          source={session.activeSource?.source ?? null}
          onClose={() => session.setActiveSource(null)}
        />
      )}
    </div>
  );
}
