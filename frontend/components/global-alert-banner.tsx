
"use client"

import { useEffect, useState } from "react"
import { AlertCircle, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { apiFetch } from "@/lib/api"
import { useRouter } from "next/navigation"

interface CriticalFailure {
  id: number
  tag: string
  equipment_id?: number
  description: string
  failure_date: string
}

export function GlobalAlertBanner() {
  const [criticalFailures, setCriticalFailures] = useState<CriticalFailure[]>([])
  const [isVisible, setIsVisible] = useState(true)
  const router = useRouter()

  useEffect(() => {
    fetchCriticalFailures()
    // Poll every 60 seconds
    const interval = setInterval(fetchCriticalFailures, 60000)
    return () => clearInterval(interval)
  }, [])

  const fetchCriticalFailures = async () => {
    try {
      // Fetch OPEN failures (M9 endpoint)
      const res = await apiFetch("/failures?status=Open")
      if (res.ok) {
        const data = await res.json()
        // Filter for "Critical" impact or severe issues
        // Assuming severity or impact logic. For now, take first 3 Open ones.
        const critical = data.filter((f: any) => f.impact === "High" || f.status === "Open").slice(0, 1)
        setCriticalFailures(critical)
        if (critical.length > 0) setIsVisible(true)
      }
    } catch (error) {
      console.error("Failed to fetch alerts", error)
    }
  }

  if (!isVisible || criticalFailures.length === 0) return null

  const failure = criticalFailures[0]

  return (
    <div className="w-full bg-white dark:bg-slate-900 border-b border-red-100 dark:border-red-900/30 shadow-sm animate-in slide-in-from-top-2">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer group" onClick={() => router.push(`/dashboard/failure-notification/edit/${failure.id}`)}>
          <div className="h-8 w-8 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center shrink-0 group-hover:bg-red-100 transition-colors">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
            <span className="font-bold text-red-700 dark:text-red-400">CRITICAL ALERT</span>
            <span className="hidden sm:inline text-slate-300">|</span>
            <span className="text-sm text-slate-600 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-slate-100 transition-colors">
              Failure detected on Tag <span className="font-mono font-medium text-slate-900 dark:text-slate-100 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-xs">{failure.tag}</span> • {new Date(failure.failure_date).toLocaleDateString()}
            </span>
          </div>
          <span className="text-xs font-medium text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity ml-2">Click to view details →</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full"
          onClick={() => setIsVisible(false)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
