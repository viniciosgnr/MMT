import { Sidebar } from "@/components/sidebar"
import { Topbar } from "@/components/topbar"
import { GlobalAlertBanner } from "@/components/global-alert-banner"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <GlobalAlertBanner />
        <Topbar />
        <main className="flex-1 overflow-auto p-4 bg-gray-50/50">
          {children}
        </main>
      </div>
    </div>
  )
}
