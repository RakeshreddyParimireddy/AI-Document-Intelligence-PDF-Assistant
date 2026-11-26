import DashboardView from "@/components/DashboardView";

// Pages behind login are shown only after the browser checks the login token,
// so Next.js can't pre-render them. This turns off its "instant navigation"
// check for this page (it only works in a server file, which is why the
// actual dashboard lives in components/DashboardView.tsx).
export const instant = false;

export default function DashboardPage() {
  return <DashboardView />;
}
