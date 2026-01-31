"use client"

import { CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export const ACTIVITY_TYPES = [
  "Plan Calibration/Inspection",
  "Execute Calibration/Inspection",
  "Take Sample",
  "Issue Report",
  "Issue Certificate",
  "Issue Uncertainty Calculation",
  "Update Flow Computer"
]

export const TYPE_COLORS: Record<string, string> = {
  "Plan Calibration/Inspection": "bg-blue-100 text-blue-700 border-blue-200",
  "Execute Calibration/Inspection": "bg-indigo-100 text-indigo-700 border-indigo-200",
  "Take Sample": "bg-purple-100 text-purple-700 border-purple-200",
  "Issue Report": "bg-green-100 text-green-700 border-green-200",
  "Issue Certificate": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "Issue Uncertainty Calculation": "bg-cyan-100 text-cyan-700 border-cyan-200",
  "Update Flow Computer": "bg-orange-100 text-orange-700 border-orange-200",
  "Mitigated": "bg-slate-100 text-slate-700 border-slate-200",
}

export function TrafficLight({ status, scheduledDate }: { status: string, scheduledDate: string }) {
  if (status === "Completed") return <CheckCircle2 className="h-4 w-4 text-green-500" />
  if (status === "Mitigated") return <div className="h-4 w-4 rounded-full bg-slate-300" />

  const now = new Date()
  const due = new Date(scheduledDate)
  const diffDays = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return <div className="h-4 w-4 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.5)]" title="Overdue" />
  if (diffDays <= 3) return <div className="h-4 w-4 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]" title="Close to Expiration" />
  return <div className="h-4 w-4 rounded-full bg-green-500" title="On Time" />
}
