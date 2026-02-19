"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Dot,
} from 'recharts'
import {

  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertCircle,
  Beaker,
  Truck,
  Upload,
  FileText,
  Search,
  Monitor,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  History,
  ShieldCheck,
  Undo2,
  Plus,
  AlertTriangle,
  Calendar,
  TrendingUp,
} from "lucide-react"
import { apiFetch } from "@/lib/api"
import { createClient } from "@/utils/supabase/client"
import { toast } from "sonner"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"

const STATUS_LINE = [
  "Planned",
  "Sampled",
  "Disembark preparation",
  "Disembark logistics",
  "Warehouse",
  "Logistics to vendor",
  "Delivered at vendor",
  "Report issued",
  "Report under validation",
  "Report approved/reproved",
  "Flow computer updated"
]

const NEXT_ACTION: Record<string, string> = {
  "Planned": "Perform sampling",
  "Sampled": "Prepare disembark",
  "Disembark preparation": "Send for logistics",
  "Disembark logistics": "Receive at warehouse",
  "Warehouse": "Ship to vendor",
  "Logistics to vendor": "Confirm delivery",
  "Delivered at vendor": "Issue lab report",
  "Report issued": "Validate report",
  "Report under validation": "Approve / Reprove",
  "Report approved/reproved": "Update flow computer",
  "Flow computer updated": "— Complete —",
}

function getDueDiffDays(dueDateStr: string | null): number | null {
  if (!dueDateStr) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dueDateStr + "T00:00:00")
  return Math.floor((due.getTime() - today.getTime()) / (1000 * 3600 * 24))
}

export default function SampleDetailPage() {
  const { id } = useParams()
  const router = useRouter()
  const [sample, setSample] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [reportValidation, setReportValidation] = useState<any>(null)

  // Interaction states
  const [isStatusDialogOpen, setIsStatusDialogOpen] = useState(false)
  const [nextStatus, setNextStatus] = useState("")
  const [statusComments, setStatusComments] = useState("")
  const [eventDate, setEventDate] = useState(new Date().toISOString().split('T')[0])
  const [dueDate, setDueDate] = useState("")
  const [evidenceUrl, setEvidenceUrl] = useState("")
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null)

  // Report Validation (PDF extraction)
  const [isUploadingReport, setIsUploadingReport] = useState(false)
  const [labResults, setLabResults] = useState<any[]>([])

  // History chart state
  const [historyParam, setHistoryParam] = useState<string>('density')
  const [historyData, setHistoryData] = useState<any[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  useEffect(() => {
    if (id) loadSample()
  }, [id])

  const loadSample = async () => {
    try {
      setIsLoading(true)
      const res = await apiFetch(`/chemical/samples/${id}`)
      if (res.ok) {
        setSample(await res.json())
      } else {
        toast.error("Failed to load sample details")
      }
    } catch (error) {
      toast.error("Failed to load sample details")
    } finally {
      setIsLoading(false)
    }
  }


  const handleUpdateStatus = async () => {
    try {
      let finalUrl = evidenceUrl

      // Upload evidence file if selected
      if (evidenceFile) {
        const toastId = toast.loading("Uploading evidence...")
        const supabase = createClient()
        const fileName = `${sample.id}_${Date.now()}_${evidenceFile.name.replace(/[^a-zA-Z0-9.]/g, '_')}`

        const { data, error } = await supabase.storage
          .from('evidence')
          .upload(fileName, evidenceFile)

        if (error) {
          toast.dismiss(toastId)
          toast.error(`Upload failed: ${error.message}`)
          return
        }

        const { data: { publicUrl } } = supabase.storage
          .from('evidence')
          .getPublicUrl(fileName)

        finalUrl = publicUrl
        toast.dismiss(toastId)
        toast.success("Evidence uploaded")
      }

      // Strict Validation Check — require justification if report validation reproved
      if (nextStatus === "Report approved/reproved" && reportValidation?.overall_status === "fail") {
        if (!statusComments || statusComments.length < 3) {
          toast.error("Validation issues found. Please provide a justification comment to proceed.")
          return
        }
      }

      const body: any = {
        status: nextStatus,
        comments: statusComments,
        user: "Current User",
        event_date: eventDate,
        url: finalUrl,
        validation_status: reportValidation?.overall_status,
      }
      if (dueDate) body.due_date = dueDate

      const res = await apiFetch(`/chemical/samples/${sample.id}/update-status`, {
        method: "POST",
        body: JSON.stringify(body)
      })

      if (res.ok) {
        toast.success(`Status updated to ${nextStatus}`)
        setIsStatusDialogOpen(false)
        setStatusComments("")
        setDueDate("")
        setEvidenceUrl("")
        loadSample()
      } else {
        toast.error("Failed to update status")
      }
    } catch (error) {
      toast.error("Failed to update status")
    }
  }



  // Lab Report PDF upload & validation
  const handleReportUpload = async (file: File) => {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Please upload a PDF file')
      return
    }
    setIsUploadingReport(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await apiFetch(`/chemical/samples/${sample.id}/validate-report`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const result = await res.json()
        setReportValidation(result)
        toast.success(`Report parsed: ${result.overall_status}`)
        // Reload sample and lab results
        loadSample()
        loadLabResults()
      } else {
        const err = await res.json()
        toast.error(err.detail || 'Failed to validate report')
      }
    } catch (error) {
      toast.error('Failed to upload and validate report')
    } finally {
      setIsUploadingReport(false)
    }
  }

  const loadLabResults = async () => {
    try {
      const res = await apiFetch(`/chemical/samples/${id}/lab-results`)
      if (res.ok) {
        setLabResults(await res.json())
      }
    } catch { }
  }

  const REPORT_STAGES = ['Report under validation', 'Report approved/reproved', 'Flow computer updated']
  useEffect(() => {
    if (id && sample && REPORT_STAGES.includes(sample.status)) {
      loadLabResults()
    } else {
      // Clear report-related state when not at a report stage
      setLabResults([])
      setHistoryData([])
      setReportValidation(null)
    }
  }, [id, sample?.status])

  // Load parameter history for chart
  const loadParameterHistory = async (param: string) => {
    if (!sample?.sample_point_id) return
    setIsLoadingHistory(true)
    try {
      const res = await apiFetch(`/chemical/sample-points/${sample.sample_point_id}/parameter-history`, {
        params: { parameter: param, limit: 15 },
      })
      if (res.ok) {
        const data = await res.json()
        // Reverse so oldest is first (chart reads left-to-right)
        setHistoryData(data.reverse())
      }
    } catch { }
    setIsLoadingHistory(false)
  }

  useEffect(() => {
    if (sample?.sample_point_id && labResults.length > 0) {
      // Auto-select first parameter that has history
      const firstParam = labResults[0]?.parameter || 'density'
      setHistoryParam(firstParam)
      loadParameterHistory(firstParam)
    }
  }, [sample?.sample_point_id, labResults])

  useEffect(() => {
    if (historyParam && sample?.sample_point_id) {
      loadParameterHistory(historyParam)
    }
  }, [historyParam])

  const getCurrentStepIndex = () => {
    return STATUS_LINE.indexOf(sample?.status || "Planned")
  }

  if (isLoading || !sample) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  const dueDiff = getDueDiffDays(sample.due_date)

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div className="h-8 w-px bg-border"></div>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              {sample.sample_id}
              <Badge variant="outline">{sample.type}</Badge>
            </h1>
            <p className="text-sm text-muted-foreground">{sample.sample_point?.tag_number} - {sample.sample_point?.description}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {getCurrentStepIndex() > 0 && (
            <Button variant="outline" size="sm" onClick={() => {
              setNextStatus(STATUS_LINE[getCurrentStepIndex() - 1])
              setIsStatusDialogOpen(true)
            }}>
              <Undo2 className="w-4 h-4 mr-2" /> Step Back
            </Button>
          )}
          {getCurrentStepIndex() < STATUS_LINE.length - 1 && (
            <Button size="sm" onClick={() => {
              setNextStatus(STATUS_LINE[getCurrentStepIndex() + 1])
              setIsStatusDialogOpen(true)
            }}>
              Next Step: {STATUS_LINE[getCurrentStepIndex() + 1]}
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>
      </div>

      {/* Stepper Visualization */}
      <Card className="border-none shadow-sm bg-muted/20">
        <CardContent className="pt-8 pb-4">
          <div className="relative flex justify-between items-start">
            <div className="absolute top-5 left-0 w-full h-0.5 bg-muted z-0"></div>
            <div
              className="absolute top-5 left-0 h-0.5 bg-primary transition-all duration-700 z-0"
              style={{ width: `${(getCurrentStepIndex() / (STATUS_LINE.length - 1)) * 100}%` }}
            ></div>

            {STATUS_LINE.map((step, idx) => {
              const isActive = idx === getCurrentStepIndex()
              const isCompleted = idx < getCurrentStepIndex()
              return (
                <div key={step} className="relative z-10 flex flex-col items-center group">
                  <div className={`
                    w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300
                    ${isCompleted ? 'bg-primary text-white' : isActive ? 'bg-primary ring-4 ring-primary/20 text-white' : 'bg-background border-2 border-muted text-muted-foreground'}
                  `}>
                    {isCompleted ? <CheckCircle2 className="w-6 h-6" /> : <span className="text-sm font-bold">{idx + 1}</span>}
                  </div>
                  <span className={`
                    mt-2 text-[10px] font-medium max-w-[80px] text-center leading-tight
                    ${isActive ? 'text-primary font-bold' : isCompleted ? 'text-foreground' : 'text-muted-foreground'}
                  `}>
                    {step}
                  </span>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">

          {/* ═══ ENRICHED PROCESS DETAILS CARD ═══ */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Sampling Process Details</CardTitle>
              <Badge variant="outline" className="w-fit">
                Step {getCurrentStepIndex() + 1} of {STATUS_LINE.length}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-5">

              {/* Action, Due Date, SLA Row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-3 rounded-lg bg-primary/5 border border-primary/10">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Next Action</Label>
                  <div className="font-bold text-primary mt-1 flex items-center gap-2">
                    <ChevronRight className="w-4 h-4" />
                    {NEXT_ACTION[sample.status] || "—"}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 border">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Due Date</Label>
                  <div className={`font-bold mt-1 flex items-center gap-2 ${dueDiff === null || sample.status === "Flow computer updated" ? "text-foreground"
                    : dueDiff < 0 ? "text-red-600"
                      : dueDiff === 0 ? "text-amber-600"
                        : "text-foreground"
                    }`}>
                    <Calendar className="w-4 h-4" />
                    {sample.due_date ? new Date(sample.due_date).toLocaleDateString() : "Not set"}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 border">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">SLA Status</Label>
                  <div className="mt-1.5">
                    {sample.status === "Flow computer updated" ? (
                      <Badge variant="outline" className="text-violet-600 border-violet-200">Complete</Badge>
                    ) : dueDiff === null ? (
                      <span className="text-muted-foreground text-sm">—</span>
                    ) : dueDiff < 0 ? (
                      <Badge variant="destructive" className="animate-pulse">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        {Math.abs(dueDiff)}d overdue
                      </Badge>
                    ) : dueDiff === 0 ? (
                      <Badge className="bg-amber-500 text-white border-none">
                        <Clock className="w-3 h-3 mr-1" />
                        Due today
                      </Badge>
                    ) : dueDiff === 1 ? (
                      <Badge variant="outline" className="text-blue-600 border-blue-200">Tomorrow</Badge>
                    ) : (
                      <Badge variant="outline" className="text-emerald-600 border-emerald-200">
                        On Track ({dueDiff}d left)
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              {/* Sample Info Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">FPSO</Label>
                  <div className="font-medium mt-0.5">{sample.sample_point?.fpso_name || '—'}</div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Sample Point</Label>
                  <div className="font-medium mt-0.5">{sample.sample_point?.tag_number || '—'}</div>
                  <div className="text-[11px] text-muted-foreground">{sample.sample_point?.description}</div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Collection Type</Label>
                  <div className="font-medium mt-0.5">{sample.type || '—'}</div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Responsible</Label>
                  <div className="font-medium mt-0.5">{sample.responsible || '—'}</div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">OSM ID</Label>
                  <div className="font-medium mt-0.5">{sample.osm_id || '—'}</div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Report #</Label>
                  <div className="font-medium mt-0.5">{sample.laudo_number || '—'}</div>
                </div>
                <div>
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Mitigated</Label>
                  <div className="mt-0.5">
                    <Badge variant={sample.mitigated ? "default" : "outline"} className={sample.mitigated ? "bg-emerald-600" : ""}>
                      {sample.mitigated ? "Yes" : "No"}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* SLA Timeline — Expected vs Actual */}
              <div>
                <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-2 block">SLA Timeline (10-10-5-5 days)</Label>
                <div className="rounded-lg border overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-muted/50">
                        <TableHead className="text-xs font-semibold">Phase</TableHead>
                        <TableHead className="text-xs font-semibold">Expected</TableHead>
                        <TableHead className="text-xs font-semibold">Actual</TableHead>
                        <TableHead className="text-xs font-semibold">SLA</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {[
                        { phase: "Sampling", expected: sample.planned_date, actual: sample.sampling_date, icon: "🧪" },
                        { phase: "Disembark", expected: sample.disembark_expected_date, actual: sample.disembark_date, icon: "🚢" },
                        { phase: "Laboratory", expected: sample.lab_expected_date, actual: sample.delivery_date, icon: "🔬" },
                        { phase: "Report", expected: sample.report_expected_date, actual: sample.report_issue_date, icon: "📋" },
                        { phase: "FC (Flow Computer)", expected: sample.fc_expected_date, actual: sample.fc_update_date ? new Date(sample.fc_update_date).toISOString().split("T")[0] : null, icon: "💻" },
                      ].map((row) => {
                        let slaStatus = "—"
                        let slaClass = "text-muted-foreground"
                        if (row.expected && row.actual) {
                          const exp = new Date(row.expected + "T00:00:00")
                          const act = new Date(row.actual + "T00:00:00")
                          const diff = Math.floor((act.getTime() - exp.getTime()) / (1000 * 3600 * 24))
                          if (diff <= 0) {
                            slaStatus = "✅ On Time"
                            slaClass = "text-emerald-600 font-semibold"
                          } else {
                            slaStatus = `⚠️ +${diff}d late`
                            slaClass = "text-red-600 font-semibold"
                          }
                        } else if (row.expected && !row.actual) {
                          const exp = new Date(row.expected + "T00:00:00")
                          const today = new Date()
                          today.setHours(0, 0, 0, 0)
                          const diff = Math.floor((exp.getTime() - today.getTime()) / (1000 * 3600 * 24))
                          if (diff < 0) {
                            slaStatus = `🔴 ${Math.abs(diff)}d overdue`
                            slaClass = "text-red-600 font-semibold animate-pulse"
                          } else if (diff === 0) {
                            slaStatus = "🟡 Due Today"
                            slaClass = "text-amber-600 font-semibold"
                          } else {
                            slaStatus = `⏳ ${diff}d remaining`
                            slaClass = "text-blue-600"
                          }
                        }
                        return (
                          <TableRow key={row.phase}>
                            <TableCell className="font-medium text-sm">
                              <span className="mr-1.5">{row.icon}</span>{row.phase}
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {row.expected ? new Date(row.expected + "T00:00:00").toLocaleDateString() : "—"}
                            </TableCell>
                            <TableCell className="text-sm">
                              {row.actual ? new Date(row.actual + "T00:00:00").toLocaleDateString() : <span className="text-muted-foreground italic">Pending</span>}
                            </TableCell>
                            <TableCell className={`text-xs ${slaClass}`}>{slaStatus}</TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* Validation Status — only show after report has been uploaded and validated */}
              {['Report under validation', 'Report approved/reproved', 'Flow computer updated'].includes(sample.status) && sample.validation_status && labResults.length > 0 && (
                <div className="p-3 rounded-lg border bg-muted/30">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Validation Status</Label>
                  <div className="mt-1">
                    <Badge variant={sample.validation_status === "Approved" ? "default" : "destructive"}>
                      {sample.validation_status}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Evidence links — only show after report has been uploaded */}
              {['Report under validation', 'Report approved/reproved', 'Flow computer updated'].includes(sample.status) && labResults.length > 0 && (sample.lab_report_url || sample.validation_report_url || sample.fc_evidence_url) && (
                <div className="p-3 rounded-lg border bg-muted/30">
                  <Label className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-2 block">Evidence & Documents</Label>
                  <div className="flex flex-wrap gap-2">
                    {sample.lab_report_url && (
                      <a href={`${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '')}${sample.lab_report_url}`} target="_blank" rel="noopener noreferrer">
                        <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white transition-colors">
                          <FileText className="w-3 h-3 mr-1" /> Lab Report
                        </Badge>
                      </a>
                    )}
                    {sample.validation_report_url && (
                      <a href={sample.validation_report_url} target="_blank" rel="noopener noreferrer">
                        <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white transition-colors">
                          <ShieldCheck className="w-3 h-3 mr-1" /> Validation Report
                        </Badge>
                      </a>
                    )}
                    {sample.fc_evidence_url && (
                      <a href={sample.fc_evidence_url} target="_blank" rel="noopener noreferrer">
                        <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white transition-colors">
                          <Monitor className="w-3 h-3 mr-1" /> FC Evidence
                        </Badge>
                      </a>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ═══ LAB REPORT ANALYSIS (PDF Upload & Validation) ═══ */}
          {(() => {
            const reportStages = ['Report under validation', 'Report approved/reproved', 'Flow computer updated']
            const showReport = reportStages.includes(sample.status)
            if (!showReport) return null

            const PARAM_LABELS: Record<string, string> = {
              density: 'Density (Massa específica)',
              rs: 'RS (Solubility Ratio)',
              fe: 'FE (Shrinkage Factor)',
              o2: 'O₂ (Oxygen)',
              density_abs_std: 'Abs. Density (Std Condition)',
              density_abs_op: 'Abs. Density (Op. Condition)',
            }

            return (
              <Card className="overflow-hidden border-blue-500/20">
                <CardHeader className="bg-blue-500/[0.03] border-b border-blue-500/10">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-500" />
                    Lab Report Analysis
                  </CardTitle>
                  <CardDescription>
                    {reportValidation || labResults.length > 0
                      ? `${reportValidation?.report_type || 'Report'} — ${reportValidation?.boletim || sample.lab_report_url || ''}`
                      : 'Upload a PVT or CRO lab report PDF to extract and validate values automatically.'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  {/* Upload zone — show if no results yet or to re-upload */}
                  {labResults.length === 0 ? (
                    <label
                      className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-xl cursor-pointer hover:border-blue-500 hover:bg-blue-500/5 transition-colors"
                      onDragOver={(e) => { e.preventDefault(); e.stopPropagation() }}
                      onDragEnter={(e) => { e.preventDefault(); e.stopPropagation() }}
                      onDragLeave={(e) => { e.preventDefault(); e.stopPropagation() }}
                      onDrop={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        const f = e.dataTransfer.files?.[0]
                        if (f) handleReportUpload(f)
                      }}
                    >
                      <input
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        onChange={(e) => {
                          const f = e.target.files?.[0]
                          if (f) handleReportUpload(f)
                        }}
                        disabled={isUploadingReport}
                      />
                      {isUploadingReport ? (
                        <>
                          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mb-3" />
                          <p className="text-sm text-muted-foreground">Parsing PDF and running validation…</p>
                        </>
                      ) : (
                        <>
                          <Upload className="w-10 h-10 text-muted-foreground/40 mb-3" />
                          <p className="text-sm font-medium">Drop lab report PDF here or click to upload</p>
                          <p className="text-xs text-muted-foreground mt-1">Supports PVT and CRO reports from GT Química</p>
                        </>
                      )}
                    </label>
                  ) : (
                    <div className="space-y-4">
                      {/* Overall status + Re-upload */}
                      {(() => {
                        const status = reportValidation?.overall_status || sample.validation_status
                        const isApproved = status === 'Approved'
                        const passCount = reportValidation?.passed_count
                          ?? labResults.filter((r: any) => r.validation_status === 'pass').length
                        const failCount = reportValidation?.failed_count
                          ?? labResults.filter((r: any) => r.validation_status === 'fail').length
                        return (
                          <div className={`p-4 rounded-lg flex items-center justify-between ${isApproved
                            ? 'bg-green-500/10 text-green-700'
                            : 'bg-red-500/10 text-red-700'
                            }`}>
                            <div className="flex items-center gap-2 font-bold">
                              {isApproved
                                ? <CheckCircle2 className="w-5 h-5" />
                                : <AlertCircle className="w-5 h-5" />}
                              Validation: {status}
                              <span className="text-xs font-normal ml-2">
                                ({passCount} pass / {failCount} fail)
                              </span>
                            </div>
                            <label className="cursor-pointer">
                              <input
                                type="file"
                                accept=".pdf"
                                className="hidden"
                                onChange={(e) => {
                                  const f = e.target.files?.[0]
                                  if (f) handleReportUpload(f)
                                }}
                              />
                              <Badge variant="outline" className="cursor-pointer hover:bg-blue-500 hover:text-white transition-colors">
                                <Upload className="w-3 h-3 mr-1" /> Re-upload
                              </Badge>
                            </label>
                          </div>
                        )
                      })()}

                      {/* Extracted values table */}
                      <div className="border rounded-lg overflow-hidden">
                        <Table>
                          <TableHeader className="bg-muted/50">
                            <TableRow>
                              <TableHead>Parameter</TableHead>
                              <TableHead>Value</TableHead>
                              <TableHead>Hist. Mean</TableHead>
                              <TableHead>2σ Range</TableHead>
                              <TableHead>Result</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {labResults.map((r: any) => {
                              const badgeClass = r.validation_status === 'pass'
                                ? 'bg-green-500 text-white hover:bg-green-600'
                                : r.validation_status === 'fail'
                                  ? 'bg-red-500 text-white hover:bg-red-600'
                                  : 'bg-yellow-500 text-white hover:bg-yellow-600'
                              const badgeLabel = r.validation_status === 'pass' ? 'Pass'
                                : r.validation_status === 'fail' ? 'Fail'
                                  : r.validation_status
                              return (
                                <TableRow key={r.id}>
                                  <TableCell className="font-medium text-sm">
                                    {PARAM_LABELS[r.parameter] || r.parameter}
                                  </TableCell>
                                  <TableCell className="font-mono text-sm">
                                    {r.value?.toFixed(4)} <span className="text-xs text-muted-foreground">{r.unit}</span>
                                  </TableCell>
                                  <TableCell className="text-sm">
                                    {r.history_mean != null ? r.history_mean.toFixed(4) : '—'}
                                  </TableCell>
                                  <TableCell className="text-xs font-mono text-muted-foreground">
                                    {r.history_mean != null && r.history_std != null
                                      ? `${(r.history_mean - 2 * r.history_std).toFixed(4)} – ${(r.history_mean + 2 * r.history_std).toFixed(4)}`
                                      : '—'}
                                  </TableCell>
                                  <TableCell>
                                    <Badge className={`rounded-full ${badgeClass}`}>
                                      {badgeLabel}
                                    </Badge>
                                  </TableCell>
                                </TableRow>
                              )
                            })}
                          </TableBody>
                        </Table>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })()}

          {/* ═══ DENSITY HISTORY CHART WITH 2σ BANDS ═══ */}
          {labResults.length > 0 && historyData.length >= 1 && (() => {
            const PARAM_LABELS: Record<string, string> = {
              density: 'Density',
              rs: 'RS',
              fe: 'FE',
              o2: 'O₂',
              density_abs_std: 'Abs. Density (Std)',
              density_abs_op: 'Abs. Density (Op)',
            }

            // Calculate mean and 2σ from history
            const values = historyData.map((d: any) => d.value)
            const mean = values.reduce((a: number, b: number) => a + b, 0) / values.length
            const variance = values.length > 1
              ? values.reduce((a: number, v: number) => a + (v - mean) ** 2, 0) / (values.length - 1)
              : 0
            const std = Math.sqrt(variance)
            const upper = mean + 2 * std
            const lower = mean - 2 * std

            // Current value from lab results
            const currentResult = labResults.find((r: any) => r.parameter === historyParam)

            // Build chart data — history + current
            const chartData = historyData.map((item: any) => ({
              date: new Date(item.date).toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' }),
              value: item.value,
              sample: item.sample_id,
              upper,
              lower,
              mean,
            }))
            if (currentResult) {
              const currentDate = sample.sampling_date
                ? new Date(sample.sampling_date + 'T00:00:00').toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' })
                : 'Current'
              chartData.push({
                date: currentDate,
                value: currentResult.value,
                sample: sample.sample_id,
                upper,
                lower,
                mean,
              })
            }

            // Y-axis domain with padding
            const allVals = [...values, currentResult?.value || mean]
            const yMin = Math.min(...allVals, lower) * 0.999
            const yMax = Math.max(...allVals, upper) * 1.001

            // Available params from lab results
            const availableParams = labResults.map((r: any) => r.parameter)

            return (
              <Card className="overflow-hidden border-emerald-500/20">
                <CardHeader className="bg-emerald-500/[0.03] border-b border-emerald-500/10">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-emerald-500" />
                        Parameter History — {PARAM_LABELS[historyParam] || historyParam}
                      </CardTitle>
                      <CardDescription>
                        Last {historyData.length} samples • μ = {mean.toFixed(4)} • σ = {std.toFixed(4)} • 2σ = [{lower.toFixed(4)} – {upper.toFixed(4)}]
                      </CardDescription>
                    </div>
                  </div>
                  {/* Parameter selector tabs */}
                  {availableParams.length > 1 && (
                    <div className="flex gap-1 mt-3 flex-wrap">
                      {availableParams.map((p: string) => (
                        <Badge
                          key={p}
                          variant={p === historyParam ? 'default' : 'outline'}
                          className={`cursor-pointer transition-colors text-xs ${p === historyParam
                            ? 'bg-emerald-600 hover:bg-emerald-700'
                            : 'hover:bg-emerald-500/10'
                            }`}
                          onClick={() => setHistoryParam(p)}
                        >
                          {PARAM_LABELS[p] || p}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardHeader>
                <CardContent className="pt-6">
                  {isLoadingHistory ? (
                    <div className="flex items-center justify-center h-[280px]">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500" />
                    </div>
                  ) : (
                    <div className="h-[280px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis
                            dataKey="date"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748b', fontSize: 11 }}
                            dy={10}
                          />
                          <YAxis
                            domain={[yMin, yMax]}
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748b', fontSize: 11 }}
                            tickFormatter={(v: number) => v.toFixed(2)}
                            width={70}
                          />
                          <Tooltip
                            contentStyle={{
                              borderRadius: '8px',
                              border: 'none',
                              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                              fontSize: '12px',
                            }}
                            formatter={(val: any) => [Number(val).toFixed(4), PARAM_LABELS[historyParam] || historyParam]}
                            labelFormatter={(label: any) => String(label)}
                          />

                          {/* 2σ band (shaded area) */}
                          <ReferenceArea
                            y1={lower}
                            y2={upper}
                            fill="#10b981"
                            fillOpacity={0.08}
                            stroke="none"
                          />

                          {/* Mean reference line */}
                          <ReferenceLine
                            y={mean}
                            stroke="#10b981"
                            strokeDasharray="4 4"
                            strokeWidth={1.5}
                            label={{ value: 'μ', position: 'right', fill: '#10b981', fontSize: 12 }}
                          />

                          {/* Upper 2σ reference line */}
                          <ReferenceLine
                            y={upper}
                            stroke="#ef4444"
                            strokeDasharray="3 3"
                            strokeWidth={1}
                            label={{ value: '+2σ', position: 'right', fill: '#ef4444', fontSize: 10 }}
                          />

                          {/* Lower 2σ reference line */}
                          <ReferenceLine
                            y={lower}
                            stroke="#ef4444"
                            strokeDasharray="3 3"
                            strokeWidth={1}
                            label={{ value: '-2σ', position: 'right', fill: '#ef4444', fontSize: 10 }}
                          />

                          {/* Data line */}
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#003D5C"
                            strokeWidth={2.5}
                            dot={(props: any) => {
                              const isLast = props.index === chartData.length - 1 && currentResult
                              return (
                                <Dot
                                  {...props}
                                  r={isLast ? 6 : 3.5}
                                  fill={isLast ? '#3b82f6' : '#003D5C'}
                                  stroke={isLast ? '#fff' : 'none'}
                                  strokeWidth={isLast ? 2 : 0}
                                />
                              )
                            }}
                            activeDot={{ r: 5, fill: '#003D5C', stroke: '#fff', strokeWidth: 2 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Legend */}
                  <div className="flex items-center justify-center gap-6 mt-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full bg-[#003D5C]" /> Historical
                    </span>
                    {currentResult && (
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded-full bg-blue-500 ring-2 ring-white" /> Current Sample
                      </span>
                    )}
                    <span className="flex items-center gap-1.5">
                      <span className="w-6 h-0.5 bg-emerald-500" style={{ borderTop: '2px dashed #10b981' }} /> Mean (μ)
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-6 h-3 bg-emerald-500/10 border border-red-400/30 rounded-sm" /> 2σ Band
                    </span>
                  </div>
                </CardContent>
              </Card>
            )
          })()}

          {/* Analysis Results & SBM Validation removed — replaced by Lab Report Analysis + Parameter History Chart above */}
        </div>

        {/* Sidebar: History & Files */}
        <div className="space-y-6">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <History className="w-5 h-5 text-primary" />
                Status History
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden">
              <ScrollArea className="h-[600px] pr-4">
                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-muted">
                  {sample.history?.slice().sort((a: any, b: any) => b.id - a.id).map((entry: any, i: number) => {
                    const conf = getStatusConfig(entry.status)
                    return (
                      <div key={entry.id} className="relative">
                        <div className={`absolute -left-[22px] top-1 w-4 h-4 rounded-full border-2 border-background ${conf.color}`}></div>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                            {new Date(entry.entered_at).toLocaleString()}
                          </span>
                          <span className="font-semibold">{entry.status}</span>
                          <p className="text-sm text-muted-foreground mt-1 bg-muted/50 p-2 rounded-md">
                            {entry.comments || 'No comments provided.'}
                          </p>
                          <span className="text-[10px] mt-1 text-primary italic">User: {entry.user || 'System'}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Status Update Dialog */}
      <Dialog open={isStatusDialogOpen} onOpenChange={setIsStatusDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-primary">
              <Plus className="w-5 h-5" /> Transition Status
            </DialogTitle>
            <DialogDescription>
              You are moving this sample to: <span className="font-bold text-foreground">"{nextStatus}"</span>
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Event Date</Label>
                <Input type="date" value={eventDate} onChange={e => setEventDate(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1.5">
                  Due Date
                  <span className="text-[10px] text-muted-foreground font-normal">(deadline for this step)</span>
                </Label>
                <Input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
                <p className="text-[10px] text-muted-foreground">Leave empty to auto-calculate from SLA</p>
              </div>
              <div className="space-y-2 col-span-2">
                <Label>Evidence (File or URL)</Label>
                <div className="flex gap-2 items-center">
                  <Input
                    type="file"
                    className="cursor-pointer file:text-primary file:font-semibold"
                    onChange={(e) => {
                      const file = e.target.files?.[0] || null
                      setEvidenceFile(file)
                      if (file) setEvidenceUrl("") // Clear URL if file selected
                    }}
                  />
                  <div className="text-xs font-bold text-muted-foreground px-2">OR</div>
                  <Input
                    placeholder="Paste SharePoint / External URL"
                    value={evidenceUrl}
                    onChange={e => {
                      setEvidenceUrl(e.target.value)
                      setEvidenceFile(null) // Clear file if URL typed
                    }}
                    disabled={!!evidenceFile}
                  />
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Internal Comments / Notes</Label>
              <Textarea
                placeholder="Describe logistics details, lab observations, or validation notes..."
                className="min-h-[100px]"
                value={statusComments}
                onChange={e => setStatusComments(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsStatusDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateStatus}>Confirm Transition</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function getStatusConfig(status: string) {
  const configs: Record<string, { color: string }> = {
    "Planned": { color: "bg-slate-400" },
    "Sampled": { color: "bg-green-600" },
    "Disembark preparation": { color: "bg-blue-500" },
    "Disembark logistics": { color: "bg-blue-600" },
    "Warehouse": { color: "bg-indigo-500" },
    "Logistics to vendor": { color: "bg-indigo-600" },
    "Delivered at vendor": { color: "bg-purple-500" },
    "Report issued": { color: "bg-amber-500" },
    "Report under validation": { color: "bg-amber-600" },
    "Report approved/reproved": { color: "bg-emerald-600" },
    "Flow computer updated": { color: "bg-violet-600" },
  }
  return configs[status] || { color: "bg-slate-400" }
}
