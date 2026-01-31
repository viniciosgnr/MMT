"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertCircle,
  Beaker,
  Truck,
  FileText,
  Search,
  Monitor,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  History,
  ShieldCheck,
  Undo2
} from "lucide-react"
import {
  fetchSampleDetails,
  updateSampleStatus,
  validateSampleResults,
  addSampleResult
} from "@/lib/api"
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

export default function SampleDetailPage() {
  const { id } = useParams()
  const router = useRouter()
  const [sample, setSample] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)

  // Interaction states
  const [isStatusDialogOpen, setIsStatusDialogOpen] = useState(false)
  const [nextStatus, setNextStatus] = useState("")
  const [statusComments, setStatusComments] = useState("")
  const [eventDate, setEventDate] = useState(new Date().toISOString().split('T')[0])
  const [evidenceUrl, setEvidenceUrl] = useState("")

  useEffect(() => {
    loadSample()
  }, [id])

  const loadSample = async () => {
    try {
      setIsLoading(true)
      const data = await fetchSampleDetails(parseInt(id as string))
      setSample(data)
    } catch (error) {
      toast.error("Failed to load sample details")
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdateStatus = async () => {
    try {
      await updateSampleStatus(sample.id, {
        status: nextStatus,
        comments: statusComments,
        user: "Current User",
        event_date: eventDate,
        url: evidenceUrl
      })
      toast.success(`Status updated to ${nextStatus}`)
      setIsStatusDialogOpen(false)
      setStatusComments("")
      setEvidenceUrl("")
      loadSample()
    } catch (error) {
      toast.error("Failed to update status")
    }
  }

  const handleSbmValidation = async () => {
    try {
      setIsValidating(true)
      const result = await validateSampleResults(sample.id)
      setValidationResult(result)
      toast.success("Validation completed")
    } catch (error) {
      toast.error("Validation failed. Ensure sample results are present.")
    } finally {
      setIsValidating(false)
    }
  }

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
          {/* Detailed Info Card */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg">Sampling Process Details</CardTitle>
              <Badge variant="outline" className="flex items-center gap-1">
                <Clock className="w-3 h-3" /> SLA Tracking
              </Badge>
            </CardHeader>
            <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-y-6 gap-x-4">
              <div>
                <Label className="text-xs text-muted-foreground">Planning Date</Label>
                <div className="font-medium">{sample.planned_date || '-'}</div>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Sampling Date</Label>
                <div className="font-medium text-green-600">{sample.sampling_date || '-'}</div>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Disembark Date</Label>
                <div className="font-medium">{sample.disembark_date || '-'}</div>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Lab Delivery</Label>
                <div className="font-medium">{sample.delivery_date || '-'}</div>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Report Issued</Label>
                <div className="font-medium">{sample.report_issue_date || '-'}</div>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">FC Updated</Label>
                <div className="font-medium text-violet-600">
                  {sample.fc_update_date ? new Date(sample.fc_update_date).toLocaleDateString() : '-'}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Validation Tool */}
          <Card className="overflow-hidden border-amber-500/20">
            <CardHeader className="bg-amber-500/[0.03] border-b border-amber-500/10 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-amber-500" />
                  SBM Statistical Validation
                </CardTitle>
                <CardDescription>Automated check against 10 previous samples (Avg ± 2σ)</CardDescription>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="hover:bg-amber-500 hover:text-white transition-colors"
                onClick={handleSbmValidation}
                disabled={isValidating}
              >
                {isValidating ? 'Processing...' : 'Run Analysis'}
              </Button>
            </CardHeader>
            <CardContent className="pt-6">
              {validationResult ? (
                <div className="space-y-4">
                  <div className={`p-4 rounded-lg flex items-center justify-between ${validationResult.overall_status === 'Approved' ? 'bg-green-500/10 text-green-700' : 'bg-red-500/10 text-red-700'}`}>
                    <div className="flex items-center gap-2 font-bold">
                      {validationResult.overall_status === 'Approved' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                      Overall Assessment: {validationResult.overall_status}
                    </div>
                    <Button variant="outline" size="sm">Export Report</Button>
                  </div>
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader className="bg-muted/50">
                        <TableRow>
                          <TableHead>Parameter</TableHead>
                          <TableHead>Current</TableHead>
                          <TableHead>Avg (Historic)</TableHead>
                          <TableHead>Expected Range (±2σ)</TableHead>
                          <TableHead>Result</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {validationResult.parameters.map((p: any) => (
                          <TableRow key={p.parameter}>
                            <TableCell className="font-medium">{p.parameter}</TableCell>
                            <TableCell>{p.current?.toFixed(3) || '-'}</TableCell>
                            <TableCell>{p.avg?.toFixed(3)}</TableCell>
                            <TableCell className="text-xs font-mono text-muted-foreground">
                              {p.range[0]?.toFixed(3)} to {p.range[1]?.toFixed(3)}
                            </TableCell>
                            <TableCell>
                              <Badge variant={p.status === 'Pass' ? 'default' : 'destructive'} className="rounded-full">
                                {p.status}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-10 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/5">
                  <FlaskConical className="w-10 h-10 mx-auto mb-2 opacity-20" />
                  <p>Run validation to see statistical analysis results.</p>
                </div>
              )}
            </CardContent>
          </Card>
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
                <Label>Evidence Link (URL)</Label>
                <Input placeholder="e.g., SharePoint link" value={evidenceUrl} onChange={e => setEvidenceUrl(e.target.value)} />
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
