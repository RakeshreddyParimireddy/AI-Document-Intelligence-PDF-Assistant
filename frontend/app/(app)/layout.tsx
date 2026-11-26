// Layout for every page that needs login: sidebar on the left, page on the right.
// "(app)" is a route group: it groups pages without adding "/app" to the URL.

import AuthProvider from "@/components/AuthProvider";
import Sidebar from "@/components/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-slate-50">{children}</main>
      </div>
    </AuthProvider>
  );
}
