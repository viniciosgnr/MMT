import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { formatDistanceToNow } from "date-fns"
import { RefreshCcw, AlertTriangle, CheckCircle, XCircle } from "lucide-react"

interface SyncStatusBadgeProps {
  status: "synced" | "warning" | "error" | "unknown" | string
  lastSyncedAt?: string
  className?: string
}

export function SyncStatusBadge({ status, lastSyncedAt, className }: SyncStatusBadgeProps) {
  const getStatusConfig = () => {
    switch (status?.toLowerCase()) {
      case "synced":
        return {
          icon: CheckCircle,
          label: "Synced",
          variant: "default" as const, // Shadcn badge variant
          color: "bg-green-500 hover:bg-green-600 border-transparent text-white"
        }
      case "warning":
        return {
          icon: AlertTriangle,
          label: "Sync Warning",
          variant: "outline" as const,
          color: "text-amber-600 border-amber-500 bg-amber-50"
        }
      case "error":
        return {
          icon: XCircle,
          label: "Sync Error",
          variant: "destructive" as const,
          color: "bg-red-500 hover:bg-red-600 border-transparent text-white"
        }
      default: // unknown
        return {
          icon: RefreshCcw,
          label: "Sync Pending",
          variant: "secondary" as const,
          color: "text-gray-500"
        }
    }
  }


  const config = getStatusConfig()
  const Icon = config.icon

  // Simple HTML title for tooltip behavior without dependencies
  const titleText = `Status: ${status}\n${lastSyncedAt ? `Last Synced: ${new Date(lastSyncedAt).toLocaleString()}` : ''}`

  return (
    <div className={cn("inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border", config.color, className)} title={titleText.trim()}>
      <Icon className="h-3.5 w-3.5" />
      <span>{config.label}</span>
      {lastSyncedAt && (
        <span className="text-[10px] opacity-80 border-l border-current pl-1.5 ml-0.5">
          {formatDistanceToNow(new Date(lastSyncedAt), { addSuffix: true })}
        </span>
      )}
    </div>
  )
}
