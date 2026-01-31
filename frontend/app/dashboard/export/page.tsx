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
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Download,
  FileArchive,
  FileSpreadsheet,
  FileText,
  Calendar,
  Filter,
  Search,
  ChevronRight,
  ChevronDown,
  Info,
  ExternalLink,
  Loader2
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

const FILE_TYPES = [
  { id: "CERTS", label: "Calibration Certificates", description: "Signed PDF documents for instruments" },
  { id: "UNCERTAINTY", label: "Uncertainty Calculations", description: "Generated and uploaded calculations" },
  { id: "EVIDENCE", label: "Flow Computer Evidence", description: "Screenshots and raw data from FC" },
  { id: "SAMPLING", label: "Sampling & Validation Reports", description: "Chemical analysis reports (M3)" },
  { id: "CHANGES", label: "Equipment Change Reports", description: "M6.3 Audit trail of swaps" }
]

export default function ExportPage() {
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [nodes, setNodes] = useState<any[]>([])
  const [selectedNodes, setSelectedNodes] = useState<number[]>([])
  const [fileTypes, setFileTypes] = useState<string[]>(["CERTS", "UNCERTAINTY"])
  const [dateRange, setDateRange] = useState({ start: "2025-01-01", end: "2025-12-31" })

  useEffect(() => {
    // Fetch hierarchy for the selection tree
    fetch(`${API_URL}/equipment/hierarchy/nodes`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setNodes(data)
        } else {
          console.error("Expected array for hierarchy nodes, got:", data)
          setNodes([])
        }
      })
      .catch(() => toast.error("Failed to load hierarchy nodes"))
  }, [])

  const handleExport = async (format: "ZIP" | "EXCEL" | "PDF") => {
    if (selectedNodes.length === 0) {
      toast.error("Please select at least one unit/system")
      return
    }

    setExporting(true)
    const payload = {
      fpso_nodes: selectedNodes,
      start_date: new Date(dateRange.start).toISOString(),
      end_date: new Date(dateRange.end).toISOString(),
      file_types: fileTypes,
      format
    }

    try {
      const res = await fetch(`${API_URL}/export/prepare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      const { job_id } = await res.json()

      toast.info("Export started. Preparing your ZIP...")

      // Poll for status
      const checkStatus = setInterval(async () => {
        const sRes = await fetch(`${API_URL}/export/status/${job_id}`)
        const statusData = await sRes.json()

        if (statusData.status === "COMPLETED") {
          clearInterval(checkStatus)
          setExporting(false)
          window.location.href = `${API_URL}/export/download/${job_id}`
          toast.success("Export ready! Downloading now...")
        } else if (statusData.status === "FAILED") {
          clearInterval(checkStatus)
          setExporting(false)
          toast.error("Export failed: " + statusData.message)
        }
      }, 3000)

    } catch (error) {
      toast.error("An error occurred during export")
      setExporting(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-slate-50/50 dark:bg-slate-950/50">
      {/* Header Area */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-6 border-b bg-white dark:bg-slate-900 shadow-sm z-10 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100 italic">M7</h1>
            <div className="h-5 w-[1px] bg-slate-200 dark:bg-slate-800 mx-1" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100 font-display">
              Export Data (M7)
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] font-bold uppercase tracking-widest bg-emerald-50 text-emerald-700 border-emerald-200/50">
              Audit Compliance Tool
            </Badge>
            <p className="text-sm text-slate-500 font-medium">Prepare documentation packages for client and government audits.</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Step 1: Asset Selection Tree */}
          <Card className="lg:col-span-1 border-slate-200 dark:border-slate-800 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100/50">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Filter className="h-4 w-4 text-blue-500" />
                Step 1: Hierarchy Selection
              </CardTitle>
              <CardDescription className="text-xs">Select FPSO, systems, or specific tags to export.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="p-3 bg-slate-50/50 border-b">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                  <Input placeholder="Search tags/systems..." className="pl-9 h-9 text-xs bg-white border-slate-200" />
                </div>
              </div>
              <div className="max-h-[500px] overflow-y-auto p-2 space-y-1">
                {/* Simplified Tree Mockup */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-slate-100 rounded-md transition-all cursor-pointer group">
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                    <span className="text-xs font-bold text-slate-700">FPSO SEPETIBA</span>
                  </div>
                  <div className="pl-6 space-y-1 border-l ml-3.5 border-slate-200">
                    {Array.isArray(nodes) && nodes.map(node => (
                      <div key={node.id} className="flex items-center gap-3 px-2 py-1.5 hover:bg-slate-50 rounded-md group">
                        <Checkbox
                          id={`node-${node.id}`}
                          checked={selectedNodes.includes(node.id)}
                          onCheckedChange={(checked) => {
                            if (checked) setSelectedNodes([...selectedNodes, node.id])
                            else setSelectedNodes(selectedNodes.filter(id => id !== node.id))
                          }}
                        />
                        <label htmlFor={`node-${node.id}`} className="text-xs text-slate-600 font-medium cursor-pointer flex-1">
                          {node.tag} <span className="text-[10px] text-slate-400 ml-1">({node.level_type})</span>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Step 2 & 3: Configuration */}
          <div className="lg:col-span-2 space-y-6">

            <div className="grid md:grid-cols-2 gap-6">
              {/* Date Filter */}
              <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
                <CardHeader className="pb-3 border-b border-slate-100/50">
                  <CardTitle className="text-sm font-bold flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-emerald-500" />
                    Step 2: Date Interval
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4 space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="text-[10px] uppercase font-bold text-slate-400">From</Label>
                      <Input
                        type="date"
                        value={dateRange.start}
                        onChange={e => setDateRange({ ...dateRange, start: e.target.value })}
                        className="h-9 text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-[10px] uppercase font-bold text-slate-400">To</Label>
                      <Input
                        type="date"
                        value={dateRange.end}
                        onChange={e => setDateRange({ ...dateRange, end: e.target.value })}
                        className="h-9 text-xs"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Data Types */}
              <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
                <CardHeader className="pb-3 border-b border-slate-100/50">
                  <CardTitle className="text-sm font-bold flex items-center gap-2">
                    <FileText className="h-4 w-4 text-orange-500" />
                    Step 3: Content Types
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4 space-y-3">
                  {FILE_TYPES.map(type => (
                    <div key={type.id} className="flex items-start gap-3 group">
                      <Checkbox
                        id={type.id}
                        checked={fileTypes.includes(type.id)}
                        onCheckedChange={(checked) => {
                          if (checked) setFileTypes([...fileTypes, type.id])
                          else setFileTypes(fileTypes.filter(t => t !== type.id))
                        }}
                      />
                      <div className="space-y-0.5 leading-none cursor-pointer" onClick={() => {
                        const checked = !fileTypes.includes(type.id);
                        if (checked) setFileTypes([...fileTypes, type.id])
                        else setFileTypes(fileTypes.filter(t => t !== type.id))
                      }}>
                        <Label htmlFor={type.id} className="text-xs font-bold text-slate-700 cursor-pointer">{type.label}</Label>
                        <p className="text-[10px] text-slate-400">{type.description}</p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Execution Card */}
            <Card className="border-blue-100 dark:border-blue-900/30 bg-blue-50/30 dark:bg-blue-950/10 shadow-sm overflow-hidden border-2">
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                  <div className="space-y-1 text-center md:text-left">
                    <h3 className="text-base font-bold text-blue-900 dark:text-blue-100 flex items-center justify-center md:justify-start gap-2">
                      <Info className="h-4 w-4 text-blue-500" />
                      Ready for Audit Export
                    </h3>
                    <p className="text-xs text-blue-700/70 dark:text-blue-400/70 max-w-sm">
                      A total of <span className="font-bold text-blue-900 dark:text-blue-200">{selectedNodes.length} units</span> selected.
                      Files will be zipped into a structured folder hierarchy for auditing.
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center justify-center gap-3">
                    <Button
                      variant="outline"
                      className="bg-white hover:bg-slate-50 border-slate-200 shadow-sm text-xs h-10 px-6 font-bold"
                      onClick={() => handleExport("EXCEL")}
                      disabled={exporting}
                    >
                      <FileSpreadsheet className="h-4 w-4 mr-2 text-emerald-600" />
                      Excel List
                    </Button>
                    <Button
                      variant="outline"
                      className="bg-white hover:bg-slate-50 border-slate-200 shadow-sm text-xs h-10 px-6 font-bold"
                      onClick={() => handleExport("PDF")}
                      disabled={exporting}
                    >
                      <FileText className="h-4 w-4 mr-2 text-red-600" />
                      PDF Report
                    </Button>
                    <Button
                      className="bg-blue-600 hover:bg-blue-700 shadow-md text-xs h-10 px-8 font-bold"
                      onClick={() => handleExport("ZIP")}
                      disabled={exporting}
                    >
                      {exporting ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <FileArchive className="h-4 w-4 mr-2" />
                          Generate Audit ZIP
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Audit Suffix Guidelines */}
            <div className="bg-slate-800 rounded-xl p-5 text-slate-300 space-y-3 shadow-inner">
              <h4 className="text-[10px] uppercase font-bold tracking-widest text-slate-500">Folder Nomenclature Standards</h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <span className="text-xs font-mono bg-slate-700 px-1.5 py-0.5 rounded text-blue-400">P</span>
                  <p className="text-[9px] text-slate-500">Primary Flowmeter</p>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-mono bg-slate-700 px-1.5 py-0.5 rounded text-blue-400">S</span>
                  <p className="text-[9px] text-slate-500">Secondary (PT/TT/DP)</p>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-mono bg-slate-700 px-1.5 py-0.5 rounded text-blue-400">OP</span>
                  <p className="text-[9px] text-slate-500">Orifice Plate</p>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-mono bg-slate-700 px-1.5 py-0.5 rounded text-blue-400">SR</span>
                  <p className="text-[9px] text-slate-500">Straight Run</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
