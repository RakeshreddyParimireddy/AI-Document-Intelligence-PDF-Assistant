"use client";

// Multi-document chat: pick several documents, then ask questions across all of them.
// Each answer's citation chips show which document and page it came from.

import { useState } from "react";
import Link from "next/link";
import ChatHistoryPicker from "@/components/ChatHistoryPicker";
import ChatWindow from "@/components/ChatWindow";
import { useDocuments } from "@/components/DocumentsProvider";
import SourcePanel from "@/components/SourcePanel";
import type { Chat } from "@/lib/api";
import { useChatSession } from "@/lib/useChatSession";

const MIN_DOCUMENTS = 2;

// Chats with two or more documents belong here (single-document chats live on each document's page)
const isMultiDocumentChat = (chat: Chat) => chat.document_ids.length >= MIN_DOCUMENTS;

export default function MultiChatView() {
  const { documents } = useDocuments();
  const readyDocuments = documents.filter((d) => d.status === "ready");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // A new chat uses the picked documents that are still ready (one may have been deleted)
  const usableSelectedIds = selectedIds.filter((id) => readyDocuments.some((d) => d.id === id));
  const session = useChatSession({
    belongsHere: isMultiDocumentChat,
    documentIdsForNewChat: usableSelectedIds,
  });

  // Which documents the open chat uses (or the ones being picked for a new chat)
  const openChat = session.chats.find((c) => c.id === session.chatId);
  const chatDocumentIds = openChat ? openChat.document_ids : selectedIds;
  const filenameOf = (id: number) => documents.find((d) => d.id === id)?.filename;

  function toggle(id: number) {
    setSelectedIds((current) =>
      current.includes(id) ? current.filter((x) => x !== id) : [...current, id],
    );
  }

  function startNewChat(id: number | null) {
    session.openChat(id);
    if (id === null) setSelectedIds([]);
  }

  let disabledReason: string | null = null;
  if (!openChat && usableSelectedIds.length < MIN_DOCUMENTS) {
    disabledReason = `Select at least ${MIN_DOCUMENTS} documents above to start`;
  } else if (openChat && !chatDocumentIds.some((id) => filenameOf(id))) {
    disabledReason = "The documents in this chat were deleted";
  }

  return (
    <div className="flex h-full">
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="space-y-3 border-b border-slate-200 bg-white px-6 py-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="min-w-0 flex-1">
              <h1 className="text-lg font-semibold text-slate-900">Multi-document chat</h1>
              <p className="text-sm text-slate-500">Ask one question across several documents.</p>
            </div>
            <ChatHistoryPicker
              chats={session.chats}
              chatId={session.chatId}
              busy={session.thinking}
              onOpen={startNewChat}
            />
          </div>

          {openChat ? (
            // An existing chat: show its documents
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-400">Documents:</span>
              {chatDocumentIds.map((id) => {
                const name = filenameOf(id);
                return name ? (
                  <Link
                    key={id}
                    href={`/documents/${id}`}
                    className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-700 hover:bg-indigo-50 hover:text-indigo-700"
                  >
                    {name}
                  </Link>
                ) : (
                  <span key={id} className="rounded-full bg-slate-50 px-2.5 py-0.5 text-xs italic text-slate-400">
                    deleted document
                  </span>
                );
              })}
            </div>
          ) : readyDocuments.length < MIN_DOCUMENTS ? (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
              You need at least {MIN_DOCUMENTS} ready documents.{" "}
              <Link href="/" className="font-medium underline">
                Upload more on the dashboard
              </Link>
              .
            </p>
          ) : (
            // A new chat: pick its documents
            <fieldset className="flex flex-wrap items-center gap-2">
              <legend className="sr-only">Documents to search</legend>
              <span className="text-xs text-slate-400">Choose documents:</span>
              {readyDocuments.map((doc) => {
                const checked = selectedIds.includes(doc.id);
                return (
                  <label
                    key={doc.id}
                    className={`flex cursor-pointer items-center gap-1.5 rounded-full px-3 py-1 text-sm ring-1 ring-inset ${
                      checked
                        ? "bg-indigo-600 text-white ring-indigo-600"
                        : "bg-white text-slate-700 ring-slate-300 hover:ring-indigo-400"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggle(doc.id)}
                      className="sr-only"
                    />
                    {checked ? "✓" : "+"} {doc.filename}
                  </label>
                );
              })}
            </fieldset>
          )}
        </header>

        <ChatWindow
          emptyTitle="Ask a question across your documents"
          messages={session.messages}
          thinking={session.thinking}
          disabledReason={disabledReason}
          error={session.error}
          onAsk={session.ask}
          activeSourceKey={session.activeSource?.key ?? null}
          onSelectSource={(key, source) => session.setActiveSource({ key, source })}
        />
      </div>

      <SourcePanel
        source={session.activeSource?.source ?? null}
        onClose={() => session.setActiveSource(null)}
      />
    </div>
  );
}
