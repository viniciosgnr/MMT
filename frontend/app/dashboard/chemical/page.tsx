"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import {
  Search,
  FlaskConical,
  FileCheck,
  Settings,
  Plus,
  ArrowRight,
  AlertCircle,
  Clock,
  CheckCircle2,
  Filter,
  Beaker,
  Truck,
  Activity,
  Calendar,
  AlertTriangle,
  MonitorCheck,
  Package,
  ClipboardList,
  Ship,
  FastForward,
  Eye,
} from "lucide-react"
import { toast } from "sonner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/api"
import { createClient } from "@/utils/supabase/client"

const stripFpsoSuffix = (tag: string | undefined): string => {
  if (!tag) return ""
  return tag.replace(/-(CDI|CDS|CDM|CDP|ESS|CPX|CDA|ADG|ATD|SEP)$/, "")
}

// ── Types ──────────────────────────────────────────────────
interface StepStat {
  name: string
  total: number
  overdue: number
  due_today: number
  due_tomorrow: number
  others: number
}

interface GroupStat {
  total: number
  overdue: number
  due_today: number
  due_tomorrow: number
  others: number
  steps: StepStat[]
}

type DashboardStats = Record<string, GroupStat>

// ── Card config ────────────────────────────────────────────
const CARD_CONFIG = [
  { key: "sampling", label: "Sampling", icon: Beaker, statuses: ["Plan", "Sample"] },
  { key: "disembark", label: "Disembark", icon: Ship, statuses: ["Disembark preparation", "Disembark logistics"] },
  { key: "logistics", label: "Logistics", icon: Truck, statuses: ["Warehouse", "Logistics to vendor", "Deliver at vendor"] },
  { key: "report", label: "Report", icon: ClipboardList, statuses: ["Report issue", "Report under validation", "Report approve/reprove"] },
  { key: "fc_update", label: "FC Update", icon: MonitorCheck, statuses: ["Flow computer update"] },
]

// ── 11 steps in order ──────────────────────────────────────
const STATUS_LINE = [
  "Plan",
  "Sample",
  "Disembark preparation",
  "Disembark logistics",
  "Warehouse",
  "Logistics to vendor",
  "Deliver at vendor",
  "Report issue",
  "Report under validation",
  "Report approve/reprove",
  "Flow computer update",
]

// ── Next action description per status ─────────────────────
const NEXT_ACTION: Record<string, string> = {
  "Plan": "Collect sample",
  "Sample": "Prepare disembark",
  "Disembark preparation": "Send for logistics",
  "Disembark logistics": "Receive at warehouse",
  "Warehouse": "Ship to vendor",
  "Logistics to vendor": "Confirm delivery",
  "Deliver at vendor": "Issue lab report",
  "Report issue": "Validate report",
  "Report under validation": "Approve / Reprove",
  "Report approve/reprove": "Update flow computer",
  "Flow computer update": "— Complete —",
}

// ── Get next status in sequence ────────────────────────────
function getNextStatus(currentStatus: string): string | null {
  const idx = STATUS_LINE.indexOf(currentStatus)
  if (idx < 0 || idx >= STATUS_LINE.length - 1) return null
  return STATUS_LINE[idx + 1]
}

// ── Color logic (card bg) ──────────────────────────────────
function getCardStyle(stat: GroupStat | undefined) {
  if (!stat || stat.total === 0) return {
    border: "border-slate-200 dark:border-slate-700",
    bg: "bg-card",
    accent: "text-slate-500",
  }
  if (stat.overdue > 0) return {
    border: "border-red-400 dark:border-red-600",
    bg: "bg-red-50 dark:bg-red-950/30",
    accent: "text-red-600",
  }
  if (stat.due_today > 0) return {
    border: "border-amber-400 dark:border-amber-600",
    bg: "bg-amber-50 dark:bg-amber-950/30",
    accent: "text-amber-600",
  }
  if (stat.due_tomorrow > 0) return {
    border: "border-blue-300 dark:border-blue-600",
    bg: "bg-blue-50 dark:bg-blue-950/30",
    accent: "text-blue-600",
  }
  return {
    border: "border-emerald-300 dark:border-emerald-600",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    accent: "text-emerald-600",
  }
}

const getStatusConfig = (status: string) => {
  const configs: Record<string, { color: string; icon: any }> = {
    "Plan": { color: "bg-slate-100 text-slate-700 border-slate-200", icon: Clock },
    "Sample": { color: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: Beaker },
    "Disembark preparation": { color: "bg-cyan-50 text-cyan-700 border-cyan-200", icon: Package },
    "Disembark logistics": { color: "bg-blue-50 text-blue-700 border-blue-200", icon: Ship },
    "Warehouse": { color: "bg-indigo-50 text-indigo-700 border-indigo-200", icon: Activity },
    "Logistics to vendor": { color: "bg-violet-50 text-violet-700 border-violet-200", icon: Truck },
    "Deliver at vendor": { color: "bg-purple-50 text-purple-700 border-purple-200", icon: FlaskConical },
    "Report issue": { color: "bg-amber-50 text-amber-700 border-amber-200", icon: FileCheck },
    "Report under validation": { color: "bg-orange-50 text-orange-700 border-orange-200", icon: Search },
    "Report approve/reprove": { color: "bg-green-50 text-green-700 border-green-200", icon: CheckCircle2 },
    "Flow computer update": { color: "bg-teal-50 text-teal-700 border-teal-200", icon: ArrowRight },
  }
  return configs[status] || { color: "bg-slate-100 text-slate-500 border-slate-200", icon: AlertCircle }
}

const getClassificationConfig = (classification: string | undefined | null) => {
  if (!classification) return { label: "—", className: "text-slate-500" }

  const lowerClass = classification.toLowerCase()
  if (lowerClass.includes("fiscal")) {
    return {
      label: classification,
      className: "bg-blue-50 text-blue-700 border border-blue-200"
    }
  }
  if (lowerClass.includes("custody")) {
    return {
      label: classification,
      className: "bg-fuchsia-50 text-fuchsia-700 border border-fuchsia-200"
    }
  }
  if (lowerClass.includes("allocation") || lowerClass.includes("apropriation") || lowerClass.includes("appropriation")) {
    return {
      label: classification,
      className: "bg-amber-50 text-amber-700 border border-amber-200"
    }
  }
  if (lowerClass.includes("operational")) {
    return {
      label: classification,
      className: "bg-cyan-50 text-cyan-700 border border-cyan-200"
    }
  }

  return {
    label: classification,
    className: "bg-slate-100 text-slate-600 border border-slate-200"
  }
}

// ── Urgency helpers ────────────────────────────────────────
function getDueDiffDays(dueDateStr: string | null): number | null {
  if (!dueDateStr) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dueDateStr.split("T")[0] + "T00:00:00")
  return Math.floor((due.getTime() - today.getTime()) / (1000 * 3600 * 24))
}

function displayDate(dateStr: string | null): string {
  if (!dateStr) return "—"
  return new Date(dateStr.split("T")[0] + "T12:00:00").toLocaleDateString()
}

function getRowUrgencyClass(dueDateStr: string | null, status: string): string {
  if (status === "Flow computer updated") return ""
  const diff = getDueDiffDays(dueDateStr)
  if (diff === null) return ""
  if (diff < 0) return "bg-red-50 dark:bg-red-950/20 border-l-4 border-l-red-500"
  if (diff === 0) return "bg-amber-50 dark:bg-amber-950/20 border-l-4 border-l-amber-500"
  if (diff === 1) return "bg-blue-50 dark:bg-blue-950/10 border-l-4 border-l-blue-400"
  return ""
}

function getUrgencyBadge(dueDateStr: string | null, status: string) {
  if (status === "Flow computer updated") {
    return <Badge variant="outline" className="text-violet-600 border-violet-200 text-[10px] px-2 py-0.5">Complete</Badge>
  }
  const diff = getDueDiffDays(dueDateStr)
  if (diff === null) return <span className="text-muted-foreground text-xs">—</span>
  if (diff < 0) {
    return (
      <Badge variant="destructive" className="text-[10px] px-2 py-0.5 animate-pulse">
        <AlertTriangle className="w-3 h-3 mr-1" />
        {Math.abs(diff)}d overdue
      </Badge>
    )
  }
  if (diff === 0) {
    return (
      <Badge className="bg-amber-500 text-white border-none text-[10px] px-2 py-0.5">
        <Clock className="w-3 h-3 mr-1" />
        Due today
      </Badge>
    )
  }
  if (diff === 1) {
    return <Badge variant="outline" className="text-blue-600 border-blue-200 text-[10px] px-2 py-0.5">Tomorrow</Badge>
  }
  return <Badge variant="outline" className="text-emerald-600 border-emerald-200 text-[10px] px-2 py-0.5">On Track</Badge>
}

// ══════════════════════════════════════════════════════════
export default function ChemicalAnalysisDashboard() {
  const router = useRouter()
  const [samples, setSamples] = useState<any[]>([])

  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [fpsoFilter, setFpsoFilter] = useState("all")
  const [categoryFilter, setCategoryFilter] = useState<string>("all")
  const [activeGroup, setActiveGroup] = useState<string | null>(null)

  // Quick-advance popover state
  const [advancingSampleId, setAdvancingSampleId] = useState<number | null>(null)

  const [isAdvancing, setIsAdvancing] = useState(false)

  useEffect(() => {
    loadData()

    const supabase = createClient()
    const channel = supabase
      .channel('chemical-dashboard')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'samples' }, () => {
        loadData()
        toast.info("Dashboard updated via Realtime")
      })
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [fpsoFilter])

  const loadData = async () => {
    try {
      setIsLoading(true)
      const fpsoParam = fpsoFilter !== "all" ? `?fpso_name=${fpsoFilter}` : ""
      const [samplesRes, statsRes] = await Promise.all([
        apiFetch(`/chemical/samples${fpsoParam}`),
        apiFetch(`/chemical/dashboard-stats${fpsoParam}`),
      ])

      if (samplesRes.ok) setSamples(await samplesRes.json())
      if (statsRes.ok) setStats(await statsRes.json())
    } catch (error) {
      toast.error("Failed to load sampling data")
    } finally {
      setIsLoading(false)
    }
  }

  // ── Quick advance handler ────────────────────────────────
  const handleQuickAdvance = async (sample: any) => {
    const next = getNextStatus(sample.status)
    if (!next) return

    try {
      setIsAdvancing(true)
      const body: any = {
        status: next,
        comments: `Quick advance from dashboard`,
        user: "Current User",
        event_date: new Date().toISOString().split("T")[0],
      }


      const res = await apiFetch(`/chemical/samples/${sample.id}/update-status`, {
        method: "POST",
        body: JSON.stringify(body),
      })

      if (res.ok) {
        toast.success(`${sample.sample_id} → ${next}`)
        setAdvancingSampleId(null)
        loadData()
      } else {
        toast.error("Failed to advance status")
      }
    } catch (error) {
      toast.error("Failed to advance status")
    } finally {
      setIsAdvancing(false)
    }
  }

  // ── Filtering ────────────────────────────────────────────
  const activeStatuses = activeGroup
    ? CARD_CONFIG.find(c => c.key === activeGroup)?.statuses || []
    : []

  const filteredSamples = samples
    .filter(s => {
      if (categoryFilter !== "all" && s.category !== categoryFilter) return false
      if (activeGroup && !activeStatuses.includes(s.status)) return false
      if (!searchQuery) return true
      const q = searchQuery.toLowerCase()
      return (
        s.sample_id?.toLowerCase().includes(q) ||
        s.sample_point?.tag_number?.toLowerCase().includes(q) ||
        s.status?.toLowerCase().includes(q)
      )
    })
    .sort((a, b) => {
      const score = (s: any) => {
        const d = getDueDiffDays(s.due_date)
        return d === null ? 999 : d
      }
      return score(a) - score(b)
    })

  // ── Legend component ─────────────────────────────────────
  const UrgencyLegend = () => (
    <div className="flex gap-2 flex-wrap mt-1">
      <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
        <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Overdue
      </span>
      <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
        <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> Today
      </span>
      <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
        <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /> Tomorrow
      </span>
      <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
        <span className="w-2 h-2 rounded-full bg-slate-300 inline-block" /> Others
      </span>
    </div>
  )

  return (
    <div className="p-6 space-y-6">
      {/* ── Header ── */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Chemical Analysis</h1>
          <p className="text-muted-foreground">
            Operator action center — track all 11 steps from sampling to FC update.
          </p>
        </div>
        <Button onClick={() => router.push("/dashboard/chemical/new")}>
          <Plus className="w-4 h-4 mr-2" />
          Plan Analysis
        </Button>
      </div>

      {/* ── FPSO Filter + Category Toggle ── */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* Category toggle */}
        <div className="flex items-center border rounded-lg overflow-hidden">
          {["all", "Coleta", "Operacional"].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${categoryFilter === cat
                ? "bg-primary text-primary-foreground"
                : "bg-muted/30 text-muted-foreground hover:bg-muted/50"
                }`}
            >
              {cat === "all" ? "All" : cat === "Coleta" ? "Collections" : "Operational"}
            </button>
          ))}
        </div>

        <Select value={fpsoFilter} onValueChange={setFpsoFilter}>
          <SelectTrigger className="w-[200px]">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue placeholder="All FPSOs" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All FPSOs</SelectItem>
            <SelectItem value="CDS - Cidade de Saquarema">CDS - Saquarema</SelectItem>
            <SelectItem value="CDM - Cidade de Maricá">CDM - Maricá</SelectItem>
            <SelectItem value="CDI - Cidade de Ilhabela">CDI - Ilhabela</SelectItem>
            <SelectItem value="CDP - Cidade de Paraty">CDP - Paraty</SelectItem>
            <SelectItem value="ESS - Espírito Santo">ESS - Espírito Santo</SelectItem>
            <SelectItem value="CPX - Capixaba">CPX - Capixaba</SelectItem>
            <SelectItem value="CDA - Cidade de Anchieta">CDA - Anchieta</SelectItem>
            <SelectItem value="ADG - Alexandre de Gusmão">ADG - Alexandre de Gusmão</SelectItem>
            <SelectItem value="ATD - Almirante Tamandaré">ATD - Almirante Tamandaré</SelectItem>
            <SelectItem value="SEP - Sepetiba">SEP - Sepetiba</SelectItem>
          </SelectContent>
        </Select>
        {activeGroup && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveGroup(null)}
            className="text-muted-foreground"
          >
            ✕ Clear filter: {CARD_CONFIG.find(c => c.key === activeGroup)?.label}
          </Button>
        )}
      </div>

      {/* ══ 5 STATUS GROUP CARDS ══ */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {CARD_CONFIG.map(card => {
          const stat = stats?.[card.key]
          const style = getCardStyle(stat)
          const isActive = activeGroup === card.key

          return (
            <Card
              key={card.key}
              className={`
                cursor-pointer transition-all duration-200 border-2
                ${style.border} ${style.bg}
                ${isActive ? "ring-2 ring-primary shadow-lg scale-[1.02]" : "hover:shadow-md hover:scale-[1.01]"}
              `}
              onClick={() => setActiveGroup(isActive ? null : card.key)}
            >
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-sm font-bold uppercase tracking-wider">
                  {card.label}
                </CardTitle>
                <card.icon className={`h-5 w-5 ${style.accent}`} />
              </CardHeader>
              <CardContent className="space-y-1.5">
                {stat ? (
                  <>
                    {stat.steps.map(step => (
                      <div key={step.name} className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground text-[11px] leading-tight" title={step.name}>
                          {step.name}
                        </span>
                        <div className="flex gap-1.5 items-center">
                          {step.overdue > 0 && (
                            <span className="bg-red-500 text-white rounded-full px-1.5 py-0 text-[10px] font-bold min-w-[18px] text-center">
                              {step.overdue}
                            </span>
                          )}
                          {step.due_today > 0 && (
                            <span className="bg-amber-500 text-white rounded-full px-1.5 py-0 text-[10px] font-bold min-w-[18px] text-center">
                              {step.due_today}
                            </span>
                          )}
                          {step.due_tomorrow > 0 && (
                            <span className="bg-blue-500 text-white rounded-full px-1.5 py-0 text-[10px] font-bold min-w-[18px] text-center">
                              {step.due_tomorrow}
                            </span>
                          )}
                          {step.others > 0 && (
                            <span className="bg-slate-300 dark:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-full px-1.5 py-0 text-[10px] font-bold min-w-[18px] text-center">
                              {step.others}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}

                    <div className="border-t pt-1.5 mt-1.5 flex items-center justify-between">
                      <span className="text-xs font-bold">{stat.total} total</span>
                      {stat.overdue > 0 && (
                        <span className="text-red-600 text-[10px] font-bold flex items-center gap-0.5">
                          <AlertTriangle className="w-3 h-3" /> {stat.overdue} overdue
                        </span>
                      )}
                    </div>

                    {/* Legend on ALL cards */}
                    <UrgencyLegend />
                  </>
                ) : (
                  <div className="text-xs text-muted-foreground animate-pulse py-2">Loading…</div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* ── Search ── */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search Sample ID, Point, or Status…"
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="text-sm text-muted-foreground">
          {filteredSamples.length} sample{filteredSamples.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* ══ MAIN LAYOUT: TABLE + SIDEBAR ══ */}
      <div>
        {/* ── Samples Table (3/4 width) ── */}
        <div className="rounded-xl border bg-card shadow-sm overflow-hidden items-start flex flex-col">
          <div className="bg-slate-50 border-b w-full px-5 py-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#003D5C]" />
            <h2 className="text-xs font-bold text-[#003D5C] tracking-wider uppercase">
              All Periodic Analyses
            </h2>
          </div>
          <Table>
            <TableHeader className="bg-muted/30">
              <TableRow className="text-[11px] uppercase tracking-wider">
                <TableHead>Metering Point</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead>Sample Point</TableHead>
                <TableHead>Well</TableHead>
                <TableHead>Type of Analysis</TableHead>
                <TableHead>Validation</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Sampling Date</TableHead>
                <TableHead>Current Status</TableHead>
                <TableHead>Action</TableHead>
                <TableHead className="w-[100px]">Due To</TableHead>
                <TableHead className="w-[110px]">SLA</TableHead>
                <TableHead className="text-right w-[80px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={13} className="text-center py-20">
                    <div className="flex flex-col items-center gap-2">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                      <span className="text-muted-foreground font-medium">Synchronizing sampling data…</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredSamples.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={13} className="text-center py-20 text-muted-foreground font-medium">
                    No samples found matching your criteria.
                  </TableCell>
                </TableRow>
              ) : (
                filteredSamples.map((sample) => {
                  const statusConf = getStatusConfig(sample.status)
                  const rowClass = getRowUrgencyClass(sample.due_date, sample.status)
                  const nextStatus = getNextStatus(sample.status)

                  return (
                    <TableRow
                      key={sample.id}
                      className={`hover:bg-muted/30 transition-colors group cursor-pointer ${rowClass}`}
                      onClick={() => router.push(`/dashboard/chemical/${sample.id}`)}
                    >
                      {/* Metering Point */}
                      <TableCell className="font-bold text-slate-700">
                        {stripFpsoSuffix(sample.meter?.tag_number) || "—"}
                      </TableCell>

                      {/* Classification */}
                      <TableCell>
                        {sample.meter?.classification ? (() => {
                          const conf = getClassificationConfig(sample.meter.classification)
                          return (
                            <span className={`text-[10px] font-medium tracking-wide uppercase px-2.5 py-1 rounded-md ${conf.className}`}>
                              {conf.label}
                            </span>
                          )
                        })() : "—"}
                      </TableCell>

                      {/* Sample Point */}
                      <TableCell>
                        <span className="text-sm font-medium">{stripFpsoSuffix(sample.sample_point?.tag_number) || "—"}</span>
                      </TableCell>

                      {/* Well (for test separator analyses) */}
                      <TableCell>
                        {sample.well ? (
                          <span className="text-sm font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">
                            {sample.well.tag}
                          </span>
                        ) : (
                          <span className="text-muted-foreground text-xs">—</span>
                        )}
                      </TableCell>

                      {/* Collection / Analysis Type */}
                      <TableCell>
                        <span className="text-sm font-medium text-slate-700">
                          {(() => {
                            if (!sample.type) return "—";

                            // Map exactly first
                            const exactMap: Record<string, string> = {
                              "Massa Específica": "Specific Mass",
                              "Densidade": "Density",
                              "Viscosidade": "Viscosity",
                              "Cromatografia": "Chromatography",
                              "Specific Mass": "Specific Mass",
                              "Density": "Density",
                              "Viscosity": "Viscosity",
                              "Chromatography": "Chromatography",
                              "BSW": "BSW",
                              "PVT": "PVT",
                              "Enxofre": "Enxofre",
                              "Sulfur": "Enxofre"
                            };
                            if (exactMap[sample.type]) return exactMap[sample.type];

                            // Fallback to substring only if not exactly matched, but prefer more specific first
                            const lowerType = sample.type.toLowerCase();
                            if (lowerType.includes("massa específica") || lowerType.includes("massa especifica")) return "Specific Mass";
                            if (lowerType.includes("densidade")) return "Density";
                            if (lowerType.includes("viscosidade")) return "Viscosity";
                            if (lowerType.includes("cromatografia")) return "Chromatography";
                            if (lowerType.includes("enxofre") || lowerType.includes("sulfur")) return "Enxofre";

                            return sample.type;
                          })()}
                        </span>
                      </TableCell>

                      {/* Validation */}
                      <TableCell>
                        <span className="text-[12px] font-medium text-slate-500">{sample.validation_party || 'Client'}</span>
                      </TableCell>

                      {/* Status */}
                      <TableCell>
                        {sample.is_active ? (
                          <span className="text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/50 px-2.5 py-1 rounded-md flex items-center justify-center w-max gap-1.5 shadow-sm">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Active
                          </span>
                        ) : (
                          <span className="text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200 px-2.5 py-1 rounded-md flex items-center justify-center w-max gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span> Inactive
                          </span>
                        )}
                      </TableCell>

                      {/* Sampling Date */}
                      <TableCell className="text-sm">
                        {sample.sampling_date
                          ? displayDate(sample.sampling_date)
                          : <span className="text-muted-foreground italic">—</span>}
                      </TableCell>

                      {/* Current Status */}
                      <TableCell>
                        <Badge variant="outline" className={`${statusConf.color} flex items-center gap-1.5 w-fit px-2.5 py-1 text-[11px] shadow-sm font-medium border`}>
                          <statusConf.icon className="w-3.5 h-3.5" />
                          {sample.status}
                        </Badge>
                      </TableCell>

                      {/* Action (next step) */}
                      <TableCell>
                        <span className="text-xs font-medium text-foreground/80">
                          {NEXT_ACTION[sample.status] || "—"}
                        </span>
                      </TableCell>

                      {/* Due Date */}
                      <TableCell>
                        {sample.due_date ? (
                          <span className={
                            getDueDiffDays(sample.due_date) !== null && getDueDiffDays(sample.due_date)! < 0
                              ? "text-red-600 font-bold"
                              : getDueDiffDays(sample.due_date) === 0
                                ? "text-amber-600 font-bold"
                                : "text-sm"
                          }>
                            {displayDate(sample.due_date)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>

                      {/* SLA / Urgency Badge */}
                      <TableCell>
                        {getUrgencyBadge(sample.due_date, sample.status)}
                      </TableCell>

                      {/* Actions — Popover for quick advance (hover) */}
                      <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                        <Popover
                          open={advancingSampleId === sample.id}
                          onOpenChange={() => { }}
                        >
                          <div
                            onMouseEnter={() => {
                              setAdvancingSampleId(sample.id)
                            }}
                            onMouseLeave={(e) => {
                              // Don't close if mouse moved into the popover content
                              const related = e.relatedTarget as HTMLElement
                              if (related?.closest?.('[data-popover-content]')) return
                              setAdvancingSampleId(null)
                            }}
                          >
                            <PopoverTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="group-hover:bg-primary group-hover:text-white transition-all"
                              >
                                Detail
                              </Button>
                            </PopoverTrigger>
                          </div>
                          <PopoverContent
                            className="w-72 p-0"
                            side="left"
                            align="center"
                            data-popover-content
                            onMouseLeave={() => setAdvancingSampleId(null)}
                          >
                            <div className="p-4 space-y-3">
                              {/* Header */}
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-sm text-primary">{sample.sample_id}</span>
                                <Badge variant="outline" className="text-[10px]">{sample.status}</Badge>
                              </div>

                              {/* Quick advance section */}
                              {nextStatus ? (
                                <div className="space-y-2 border-t pt-3">
                                  <div className="flex items-center gap-2 text-xs">
                                    <FastForward className="w-3.5 h-3.5 text-primary" />
                                    <span className="font-semibold">Advance to:</span>
                                    <span className="text-primary font-bold">{nextStatus}</span>
                                  </div>

                                  {/* Due Date input */}
                                  <div className="p-2 rounded-md bg-muted/50 border">
                                    <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                                      <Calendar className="w-3 h-3" />
                                      Due date auto-calculated from SLA (10-10-5-5 days)
                                    </p>
                                  </div>

                                  <Button
                                    className="w-full h-8 text-xs"
                                    disabled={isAdvancing}
                                    onClick={() => handleQuickAdvance(sample)}
                                  >
                                    {isAdvancing ? (
                                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2" />
                                    ) : (
                                      <FastForward className="w-3 h-3 mr-2" />
                                    )}
                                    Confirm Advance
                                  </Button>
                                </div>
                              ) : (
                                <div className="text-xs text-emerald-600 font-semibold border-t pt-3 flex items-center gap-1">
                                  <CheckCircle2 className="w-4 h-4" />
                                  Lifecycle complete
                                </div>
                              )}

                              {/* View detail link */}
                              <div className="border-t pt-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="w-full text-xs"
                                  onClick={() => router.push(`/dashboard/chemical/${sample.id}`)}
                                >
                                  <Eye className="w-3 h-3 mr-2" />
                                  Open Full Detail
                                </Button>
                              </div>
                            </div>
                          </PopoverContent>
                        </Popover>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>

      </div>
    </div>
  )
}
