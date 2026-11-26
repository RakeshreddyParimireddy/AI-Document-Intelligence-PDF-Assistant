// Shared chat logic, used by the single-document chat and the multi-document chat:
// chat history, the open chat's messages, asking a question, and the selected citation.

import { useCallback, useEffect, useRef, useState } from "react";
import type { SourceGroup } from "@/components/CitationChip";
import { askQuestion, createChat, listChats, listMessages, type Chat, type Message } from "@/lib/api";

function errorText(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback;
}

export function useChatSession({
  belongsHere,
  documentIdsForNewChat,
}: {
  // Which of the user's chats to show in this page's history.
  // Must be a stable function (wrap it in useCallback).
  belongsHere: (chat: Chat) => boolean;
  // Documents a new chat is created with, when its first question is asked
  documentIdsForNewChat: number[];
}) {
  const [chats, setChats] = useState<Chat[]>([]); // newest first
  const [chatId, setChatId] = useState<number | null>(null); // null = new, unsaved chat
  const [messages, setMessages] = useState<Message[]>([]);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<{ key: string; source: SourceGroup } | null>(null);
  // Chat we just created while asking: its messages are already on screen, don't reload them
  const justCreatedChatId = useRef<number | null>(null);

  // Load chat history; open the newest chat if nothing is selected yet
  useEffect(() => {
    let cancelled = false;
    listChats()
      .then((all) => {
        if (cancelled) return;
        const mine = all.filter(belongsHere);
        setChats(mine);
        if (mine.length > 0) setChatId((current) => current ?? mine[0].id);
      })
      .catch((err) => {
        if (!cancelled) setError(errorText(err, "Could not load chats"));
      });
    return () => {
      cancelled = true;
    };
  }, [belongsHere]);

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

  // Switch to another chat (or null for a new one)
  const openChat = useCallback((id: number | null) => {
    justCreatedChatId.current = null;
    setChatId(id);
    setMessages([]);
    setActiveSource(null);
    setError(null);
  }, []);

  // Returns true if the question was answered
  async function ask(question: string): Promise<boolean> {
    setError(null);
    setThinking(true);
    // Show the question immediately (temporary negative id)
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
        id = (await createChat(documentIdsForNewChat)).id;
        justCreatedChatId.current = id;
        setChatId(id);
      }
      const answer = await askQuestion(id, question);
      setMessages((current) => [...current, answer]);
      // Refresh the history list (a new chat gets its title from the first question)
      listChats()
        .then((all) => setChats(all.filter(belongsHere)))
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

  return {
    chats,
    chatId,
    messages,
    thinking,
    error,
    activeSource,
    setActiveSource,
    openChat,
    ask,
  };
}
