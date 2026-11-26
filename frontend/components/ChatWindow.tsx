"use client";

// The list of messages plus the question box.

import { useEffect, useRef, useState } from "react";
import CitationChip, { type SourceGroup } from "@/components/CitationChip";
import type { Citation, Message } from "@/lib/api";

// Several citations can point to the same page; show one chip per document + page
export function groupCitations(citations: Citation[]): SourceGroup[] {
  const groups = new Map<string, SourceGroup>();
  for (const c of citations) {
    const key = `${c.document_id}:${c.page}`;
    const group = groups.get(key);
    if (group) group.snippets.push(c.snippet);
    else
      groups.set(key, {
        documentId: c.document_id,
        document: c.document,
        page: c.page,
        snippets: [c.snippet],
      });
  }
  return [...groups.values()];
}

function sourceKey(messageId: number, source: SourceGroup) {
  return `${messageId}:${source.documentId}:${source.page}`;
}

type Props = {
  messages: Message[];
  thinking: boolean; // waiting for an answer
  disabledReason: string | null; // why asking is not possible right now
  error: string | null;
  onAsk: (question: string) => Promise<boolean>; // true if it was sent successfully
  activeSourceKey: string | null;
  onSelectSource: (key: string, source: SourceGroup) => void;
};

export default function ChatWindow({
  messages,
  thinking,
  disabledReason,
  error,
  onAsk,
  activeSourceKey,
  onSelectSource,
}: Props) {
  const [question, setQuestion] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Keep the newest message in view
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, thinking]);

  async function send() {
    const text = question.trim();
    if (!text || thinking || disabledReason) return;
    setQuestion("");
    const ok = await onAsk(text);
    if (!ok) setQuestion(text); // give the question back so it can be retried
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Messages */}
      <div className="flex-1 space-y-6 overflow-y-auto px-6 py-6">
        {messages.length === 0 && !thinking && (
          <div className="mx-auto mt-16 max-w-md text-center">
            <p className="text-lg font-medium text-slate-800">Ask anything about this document</p>
            <p className="mt-1 text-sm text-slate-500">
              Answers come only from the document, with the pages they came from.
            </p>
          </div>
        )}

        {messages.map((message) =>
          message.role === "user" ? (
            <div key={message.id} className="flex justify-end">
              <p className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2.5 text-sm text-white">
                {message.content}
              </p>
            </div>
          ) : (
            <div key={message.id} className="flex gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">
                AI
              </span>
              <div className="max-w-[80%] space-y-2">
                <p className="whitespace-pre-wrap rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-2.5 text-sm leading-relaxed text-slate-800">
                  {message.content}
                </p>
                {message.citations.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {groupCitations(message.citations).map((source) => {
                      const key = sourceKey(message.id, source);
                      return (
                        <CitationChip
                          key={key}
                          source={source}
                          active={key === activeSourceKey}
                          onClick={() => onSelectSource(key, source)}
                        />
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ),
        )}

        {thinking && (
          <div className="flex gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">
              AI
            </span>
            <p className="flex items-center gap-1 rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3">
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:150ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:300ms]" />
              <span className="sr-only">Thinking…</span>
            </p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Question box */}
      <div className="border-t border-slate-200 bg-white px-6 py-4">
        {error && (
          <p role="alert" className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex items-end gap-3"
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              // Enter sends, Shift+Enter adds a new line
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={1}
            maxLength={1000}
            disabled={Boolean(disabledReason)}
            placeholder={disabledReason ?? "Ask a question… (Enter to send)"}
            className="max-h-40 min-h-[42px] flex-1 resize-y rounded-xl border border-slate-300 px-4 py-2.5 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 disabled:bg-slate-50"
          />
          <button
            type="submit"
            disabled={!question.trim() || thinking || Boolean(disabledReason)}
            className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}
