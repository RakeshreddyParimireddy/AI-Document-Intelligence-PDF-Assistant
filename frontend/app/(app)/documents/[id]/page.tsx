import { Suspense } from "react";
import DocumentWorkspace from "@/components/DocumentWorkspace";

// Shown only after the browser-side login check, so it can't be pre-rendered.
export const instant = false;

function Loading() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
    </div>
  );
}

// /documents/123 -> the workspace for document 123.
// The id is only known when the page is visited, so reading it sits inside <Suspense>.
export default function DocumentPage({ params }: PageProps<"/documents/[id]">) {
  return (
    <Suspense fallback={<Loading />}>
      {params.then(({ id }) => (
        // key: start fresh when switching to another document
        <DocumentWorkspace key={id} documentId={Number(id)} />
      ))}
    </Suspense>
  );
}
