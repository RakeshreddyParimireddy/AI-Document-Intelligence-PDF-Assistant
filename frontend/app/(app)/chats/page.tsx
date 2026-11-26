import MultiChatView from "@/components/MultiChatView";

// Shown only after the browser-side login check, so it can't be pre-rendered.
export const instant = false;

export const metadata = { title: "Multi-document chat · DocuMind" };

export default function ChatsPage() {
  return <MultiChatView />;
}
