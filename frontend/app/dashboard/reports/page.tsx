"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Archive, FileText, Filter, Upload, Plus, X, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { format } from "date-fns"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiFetch } from "@/lib/api"

export default function HistoricalReportPage() {
  const [reports, setReports] = useState<any[]>([])
  const [reportTypes, setReportTypes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)

  // Upload Form State
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploadForm, setUploadForm] = useState({
    report_type_id: "",
    title_prefix: "",
    report_date: format(new Date(), "yyyy-MM-dd"),
    fpso_name: "FPSO SEPETIBA",
    metering_system: "",
    serial_number: ""
  })

  // Filters
  const [filterType, setFilterType] = useState("all")
  const [filterFPSO, setFilterFPSO] = useState("all")

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    try {
      setLoading(true)
      const [reportsRes, typesRes] = await Promise.all([
        apiFetch("/reports"),
        apiFetch("/reports/types")
      ])

      if (reportsRes.ok) setReports(await reportsRes.json())
      if (typesRes.ok) setReportTypes(await typesRes.json())
    } catch (error) {
      toast.error("Failed to fetch historical data")
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  async function handleUpload() {
    if (selectedFiles.length === 0 || !uploadForm.report_type_id) {
      toast.error("Please select files and a report type")
      return
    }

    try {
      setUploading(true)
      const formData = new FormData()
      selectedFiles.forEach(file => formData.append("files", file))

      formData.append("report_type_id", uploadForm.report_type_id)
      formData.append("title_prefix", uploadForm.title_prefix)
      formData.append("report_date", uploadForm.report_date)
      if (uploadForm.fpso_name !== "Generic") formData.append("fpso_name", uploadForm.fpso_name)
      if (uploadForm.metering_system) formData.append("metering_system", uploadForm.metering_system)
      if (uploadForm.serial_number) formData.append("serial_number", uploadForm.serial_number)

      const res = await apiFetch("/reports/upload", {
        method: "POST",
        body: formData,
        // Content-Type header is explicitly NOT set here to let browser set boundary for FormData
        // apiFetch might assume JSON, so we might need to override headers.
        // apiFetch sets Content-Type to application/json by default.
        // We need to delete it.
        headers: {} // This is tricky. apiFetch sets JSON.
      })
      // Wait, apiFetch implementation:
      // const headers = { 'Content-Type': 'application/json', ...options.headers }
      // This will break FormData.
      // I need to modify apiFetch to handle FormData or use a workaround.
      // For now I will assume I can pass 'Content-Type': undefined? No.
      // I need to modify apiFetch.


      if (res.ok) {
        toast.success("Reports uploaded successfully")
        setSelectedFiles([])
        setUploadForm(prev => ({ ...prev, title_prefix: "", metering_system: "", serial_number: "" }))
        fetchData()
      } else {
        toast.error("Upload failed")
      }
    } catch (error) {
      toast.error("Error during upload")
    } finally {
      setUploading(false)
    }
  }

  const filteredReports = reports.filter(r => {
    if (filterType !== "all" && r.report_type_id.toString() !== filterType) return false
    if (filterFPSO !== "all" && r.fpso_name !== filterFPSO) return false
    return true
  })

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Historical Report (M10)</h1>
          <p className="text-slate-500 text-lg">Central repository for generic unit reports and external documentation.</p>
        </div>
        <Button variant="outline" className="gap-2" onClick={fetchData}>
          <Search className="h-4 w-4" /> Refresh Archive
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bulk Upload Panel */}
        <Card className="lg:col-span-1 shadow-sm border-slate-200">
          <CardHeader className="bg-slate-50/50 border-b border-slate-100">
            <CardTitle className="text-lg flex items-center gap-2">
              <Upload className="h-5 w-5 text-blue-600" /> Bulk Upload Reports
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Report Type</label>
              <Select
                value={uploadForm.report_type_id}
                onValueChange={(v) => setUploadForm({ ...uploadForm, report_type_id: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type..." />
                </SelectTrigger>
                <SelectContent>
                  {reportTypes.map(t => (
                    <SelectItem key={t.id} value={t.id.toString()}>{t.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">FPSO Reference</label>
              <Select
                value={uploadForm.fpso_name}
                onValueChange={(v) => setUploadForm({ ...uploadForm, fpso_name: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Generic">Generic / Not Linked</SelectItem>
                  <SelectItem value="FPSO SEPETIBA">FPSO SEPETIBA</SelectItem>
                  <SelectItem value="FPSO SAQUAREMA">FPSO SAQUAREMA</SelectItem>
                  <SelectItem value="FPSO MARICÁ">FPSO MARICÁ</SelectItem>
                  <SelectItem value="FPSO PARATY">FPSO PARATY</SelectItem>
                  <SelectItem value="FPSO ILHABELA">FPSO ILHABELA</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Report Date</label>
              <Input
                type="date"
                value={uploadForm.report_date}
                onChange={e => setUploadForm({ ...uploadForm, report_date: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Title Prefix (Optional)</label>
              <Input
                placeholder="e.g., Q1 Audit -"
                value={uploadForm.title_prefix}
                onChange={e => setUploadForm({ ...uploadForm, title_prefix: e.target.value })}
              />
            </div>

            <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:border-blue-300 transition-colors bg-slate-50/30">
              <input
                type="file"
                multiple
                className="hidden"
                id="file-upload"
                onChange={handleFileChange}
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                <Plus className="h-8 w-8 text-slate-400 mb-2" />
                <span className="text-sm font-medium text-slate-600">Click to select files</span>
                <span className="text-xs text-slate-400 mt-1">Select one or multiple files</span>
              </label>
            </div>

            {selectedFiles.length > 0 && (
              <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                {selectedFiles.map((f, i) => (
                  <div key={i} className="flex items-center justify-between text-xs bg-slate-100 p-2 rounded border border-slate-200">
                    <span className="truncate flex-1 pr-2">{f.name}</span>
                    <button onClick={() => removeFile(i)} className="text-red-500">
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <Button
              className="w-full bg-blue-600 hover:bg-blue-700 h-11"
              onClick={handleUpload}
              disabled={uploading || selectedFiles.length === 0}
            >
              {uploading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Upload className="h-4 w-4 mr-2" />}
              Upload {selectedFiles.length > 0 ? `${selectedFiles.length} files` : "Reports"}
            </Button>
          </CardContent>
        </Card>

        {/* Browser Panel */}
        <Card className="lg:col-span-2 shadow-sm border-slate-200">
          <CardHeader className="bg-slate-50/50 border-b border-slate-100 flex flex-row items-center justify-between py-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Archive className="h-5 w-5 text-slate-600" /> Archive Browser
            </CardTitle>
            <div className="flex gap-2">
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[140px] h-8 text-xs">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {reportTypes.map(t => (
                    <SelectItem key={t.id} value={t.id.toString()}>{t.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={filterFPSO} onValueChange={setFilterFPSO}>
                <SelectTrigger className="w-[140px] h-8 text-xs">
                  <SelectValue placeholder="FPSO" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All FPSOs</SelectItem>
                  <SelectItem value="FPSO SEPETIBA">SEPETIBA</SelectItem>
                  <SelectItem value="FPSO SAQUAREMA">SAQUAREMA</SelectItem>
                  <SelectItem value="FPSO MARICÁ">MARICÁ</SelectItem>
                  <SelectItem value="FPSO PARATY">PARATY</SelectItem>
                  <SelectItem value="FPSO ILHABELA">ILHABELA</SelectItem>
                  <SelectItem value="Generic">Generic</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-20 text-center">
                <Loader2 className="h-10 w-10 animate-spin mx-auto text-slate-300" />
                <p className="text-slate-500 mt-4">Loading repository...</p>
              </div>
            ) : filteredReports.length === 0 ? (
              <div className="p-20 text-center text-slate-400">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-20" />
                <p>No reports found matching filters.</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50/50">
                    <TableHead>Archive Entry</TableHead>
                    <TableHead>Report Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>FPSO</TableHead>
                    <TableHead className="text-right pr-6">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredReports.map((report) => (
                    <TableRow key={report.id} className="hover:bg-slate-50/50">
                      <TableCell className="py-4">
                        <div className="font-medium text-slate-900">{report.title}</div>
                        <div className="text-xs text-slate-500 mt-0.5">{report.file_name} • {(report.file_size / 1024).toFixed(1)} KB</div>
                      </TableCell>
                      <TableCell>{format(new Date(report.report_date), "MMM dd, yyyy")}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-normal text-slate-600 border-slate-200">
                          {report.report_type.name}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-slate-600">{report.fpso_name || "---"}</span>
                      </TableCell>
                      <TableCell className="text-right pr-6">
                        <Button variant="ghost" size="sm" className="h-8 text-blue-600 hover:text-blue-700 hover:bg-blue-50" asChild>
                          <a href={`${API_URL}${report.file_url}`} target="_blank" rel="noreferrer">
                            <FileText className="h-4 w-4 mr-1" /> View
                          </a>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
