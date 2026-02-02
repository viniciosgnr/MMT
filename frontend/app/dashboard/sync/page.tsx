"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  RefreshCw,
  CheckCircle2,
  XCircle,
  Database,
  Server,
  Upload,
  Activity,
  Plus,
  FileText,
  Clock,
  HardDrive
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api"
import { SyncSourceDialog } from "./sync-source-dialog"

export default function SynchronizationPage() {
  const [sources, setSources] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [sourceDialogOpen, setSourceDialogOpen] = useState(false)

  const fetchData = async () => {
    try {
      const [sourcesRes, jobsRes] = await Promise.all([
        apiFetch("/sync/sources"),
        apiFetch("/sync/jobs")
      ])

      if (sourcesRes.ok) {
        setSources(await sourcesRes.json())
      } else {
        setSources([])
      }

      if (jobsRes.ok) {
        setJobs(await jobsRes.json())
      } else {
        setJobs([])
      }
    } catch (error) {
      toast.error("Failed to fetch synchronization data")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>, sourceId: number) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await apiFetch(`/sync/upload?source_id=${sourceId}`, {
        method: "POST",
        body: formData,
      })
      if (res.ok) {
        toast.success("Data dump uploaded successfully")
        fetchData()
      } else {
        toast.error("Failed to process sync file")
      }
    } catch (error) {
      toast.error("Upload error")
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-slate-50/50 dark:bg-slate-950/50">
      {/* Header Area */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-6 border-b bg-white dark:bg-slate-900 shadow-sm z-10 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100 italic">M5</h1>
            <div className="h-5 w-[1px] bg-slate-200 dark:bg-slate-800 mx-1" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100 font-display">
              Synchronization Data (M5)
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] font-bold uppercase tracking-widest bg-blue-50/50 text-blue-700 border-blue-200/50">
              Contractor Module
            </Badge>
            <p className="text-sm text-slate-500 font-medium">Manage offshore HMI connections and data dumps</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchData} className="bg-white hover:bg-slate-50 border-slate-200 shadow-sm transition-all h-9 px-4">
            <RefreshCw className={cn("h-4 w-4 mr-2 text-blue-500", loading && "animate-spin")} />
            Refresh
          </Button>
          <Button size="sm" className="bg-blue-600 hover:bg-blue-700 shadow-sm h-9 px-4" onClick={() => setSourceDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Source
          </Button>
        </div>
      </div>

      <SyncSourceDialog
        open={sourceDialogOpen}
        onOpenChange={setSourceDialogOpen}
        onCreated={fetchData}
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {/* Active Sources Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {sources.length === 0 && !loading && (
            <Card className="col-span-full border-dashed border-2 flex flex-col items-center justify-center p-12 bg-slate-50/50">
              <Database className="h-10 w-10 text-slate-300 mb-4" />
              <p className="text-slate-500 font-medium">No synchronization sources registered yet.</p>
              <p className="text-xs text-slate-400 mt-1">Add your first Flow Computer or PI server connection to begin.</p>
            </Card>
          )}

          {sources.map((source) => (
            <Card key={source.id} className="group relative overflow-hidden transition-all hover:shadow-md border-slate-200 dark:border-slate-800">
              <div className="absolute top-0 left-0 w-1 h-full bg-blue-500" />
              <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
                <div className="space-y-1">
                  <CardTitle className="text-sm font-bold uppercase tracking-wider text-slate-500">{source.name}</CardTitle>
                  <CardDescription className="text-xs flex items-center gap-1.5 font-medium">
                    <Server className="h-3 w-3" />
                    {source.type.replace("_", " ")}
                  </CardDescription>
                </div>
                <div className={cn(
                  "h-2.5 w-2.5 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.4)]",
                  source.is_active ? "bg-green-500 animate-pulse" : "bg-slate-300"
                )} />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                    <Clock className="h-3 w-3" />
                    Last Ingestion
                  </div>
                  <Badge variant="secondary" className="bg-slate-200 text-slate-900 border border-slate-300 text-[10px] font-bold shadow-sm px-2">
                    Today, 10:45
                  </Badge>
                </div>

                <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                  <label
                    htmlFor={`upload-${source.id}`}
                    className="flex items-center justify-center gap-2 w-full py-2 px-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/10 hover:border-blue-200 transition-all group/btn"
                  >
                    <HardDrive className="h-4 w-4 text-slate-400 group-hover/btn:text-blue-500" />
                    <span className="text-xs font-bold text-slate-600 dark:text-slate-300 group-hover/btn:text-blue-600">Manual USB Dump</span>
                    <input
                      type="file"
                      id={`upload-${source.id}`}
                      className="hidden"
                      onChange={(e) => handleFileUpload(e, source.id)}
                      disabled={uploading}
                    />
                  </label>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Sync Jobs / History */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden rounded-xl bg-white dark:bg-slate-900">
          <CardHeader className="bg-slate-50/50 dark:bg-slate-900/50 border-b border-slate-200/60 flex flex-row items-center justify-between px-6 py-4">
            <div className="space-y-1">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-500" />
                Sync History & Data Ingestion Logs
              </CardTitle>
              <CardDescription className="text-xs">Real-time audit trail of all automated and manual synchronization activities.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50/30 dark:bg-slate-950/30 hover:bg-transparent">
                  <TableHead className="w-[180px] text-[10px] font-bold uppercase tracking-widest pl-6">Timestamp</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-widest">Source</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-widest text-center">Records</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-widest">Status</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-widest pr-6">Performance Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="h-32 text-center text-slate-400 italic text-sm">
                      No ingestion jobs recorded yet.
                    </TableCell>
                  </TableRow>
                )}
                {jobs.map((job) => (
                  <TableRow key={job.id} className="group hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                    <TableCell className="text-[11px] font-mono text-slate-500 pl-6">
                      {new Date(job.start_time).toLocaleString()}
                    </TableCell>
                    <TableCell className="font-semibold text-slate-700 dark:text-slate-200 text-sm">
                      {job.source?.name || `Source #${job.source_id}`}
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400 text-[10px] font-bold">
                        {job.records_processed?.toLocaleString()}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[10px] font-bold uppercase py-0 px-2",
                          job.status === "Synced" ? "bg-green-50 text-green-700 border-green-200" : "bg-red-50 text-red-700 border-red-200"
                        )}
                      >
                        {job.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="pr-6">
                      <div className="flex items-center gap-2">
                        <FileText className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-[11px] text-slate-500 truncate max-w-[250px]">
                          {job.artifact_path || "Live Ingestion"} • Dur: 0.4s
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
