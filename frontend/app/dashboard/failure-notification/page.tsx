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
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { AlertCircle, CheckCircle2, Clock, Download, Mail, Plus, ShieldCheck, FileText, FileSpreadsheet } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import { apiFetch } from "@/lib/api"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export default function FailureNotificationPage() {
  const [failures, setFailures] = useState<any[]>([])
  const [emailLists, setEmailLists] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("list")
  const [newEmail, setNewEmail] = useState({ fpso: "FPSO SEPETIBA", email: "" })

  const [formData, setFormData] = useState({
    fpso_name: "FPSO SEPETIBA",
    tag: "",
    equipment_id: 1,
    failure_date: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
    description: "",
    impact: "Medium",
    estimated_volume_impact: 0,
    corrective_action: "",
    responsible: "Marcos G.",
    anp_classification: "Tolerável"
  })

  useEffect(() => {
    fetchFailures()
    fetchEmailLists()
  }, [])

  const fetchFailures = async () => {
    try {
      const res = await apiFetch("/failures")
      if (res.ok) setFailures(await res.json())
    } catch (e) { toast.error("Failed to load failures") }
    finally { setLoading(false) }
  }

  const fetchEmailLists = async () => {
    try {
      const res = await apiFetch("/failures/config/emails")
      if (res.ok) setEmailLists(await res.json())
    } catch (e) { }
  }

  const handleCreate = async () => {
    try {
      const res = await apiFetch("/failures", {
        method: "POST",
        body: JSON.stringify(formData)
      })
      if (res.ok) {
        toast.success("Notification created as Draft")
        fetchFailures()
        setActiveTab("list")
      }
    } catch (e) { toast.error("Error creating notification") }
  }

  const handleApprove = async (id: number) => {
    try {
      const res = await apiFetch(`/failures/${id}/approve`, {
        method: "POST",
        body: JSON.stringify({ approved_by: "Marcos G. (ME)" })
      })
      if (res.ok) {
        toast.success("Approved! Reports sent to distribution list.")
        fetchFailures()
      }
    } catch (e) { toast.error("Approval failed") }
  }

  const handleAddEmail = async () => {
    try {
      const res = await apiFetch("/failures/config/emails", {
        method: "POST",
        body: JSON.stringify({ fpso_name: newEmail.fpso, email: newEmail.email })
      })
      if (res.ok) {
        toast.success("Email added to distribution list")
        setNewEmail({ ...newEmail, email: "" })
        fetchEmailLists()
      }
    } catch (e) { }
  }

  const exportReport = (id: string, format: 'PDF' | 'Excel') => {
    toast.info(`Generating ${format} for ${id}...`)
    // Mock download
    setTimeout(() => toast.success(`${format} report downloaded.`), 1000)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#003D5C]">Failure Notification (M9)</h1>
          <p className="text-muted-foreground">ANP Res. 18/2014 Compliance Management</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-slate-100 p-1">
          <TabsTrigger value="list" className="data-[state=active]:bg-white">Notifications</TabsTrigger>
          <TabsTrigger value="new" className="data-[state=active]:bg-white">New Failure</TabsTrigger>
          <TabsTrigger value="config" className="data-[state=active]:bg-white">Email Distribution</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="mt-4">
          <Card className="border-none shadow-sm ring-1 ring-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Event Log</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader className="bg-slate-50">
                  <TableRow>
                    <TableHead>FPSO</TableHead>
                    <TableHead>Tag</TableHead>
                    <TableHead>Impact</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>ANP Class</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {failures.map((f) => (
                    <TableRow key={f.id} className="hover:bg-slate-50/50">
                      <TableCell className="font-medium">{f.fpso_name}</TableCell>
                      <TableCell>{f.tag}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className={cn(
                          f.impact === 'High' ? "bg-red-50 text-red-700" : "bg-blue-50 text-blue-700"
                        )}>{f.impact}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={cn(
                          f.status === 'Approved' ? "bg-green-100 text-green-800" : "bg-slate-100 text-slate-800"
                        )}>{f.status}</Badge>
                      </TableCell>
                      <TableCell>{f.anp_classification}</TableCell>
                      <TableCell className="text-right space-x-2">
                        {f.status === 'Draft' && (
                          <Button size="sm" variant="outline" className="text-green-600 border-green-200 hover:bg-green-50" onClick={() => handleApprove(f.id)}>
                            <ShieldCheck className="h-4 w-4 mr-1" /> Approve
                          </Button>
                        )}
                        <Button size="icon" variant="ghost" title="Export PDF" onClick={() => exportReport(f.id, 'PDF')}>
                          <FileText className="h-4 w-4 text-red-500" />
                        </Button>
                        <Button size="icon" variant="ghost" title="Export Excel" onClick={() => exportReport(f.id, 'Excel')}>
                          <FileSpreadsheet className="h-4 w-4 text-green-600" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {failures.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-slate-400">No failures records found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="new" className="mt-4">
          <Card className="max-w-3xl mx-auto border-none shadow-lg">
            <CardHeader className="bg-[#003D5C] text-white rounded-t-lg">
              <CardTitle>Report New Failure (ANP RTNF)</CardTitle>
              <CardDescription className="text-slate-300">Enter failure details according to Resolution 18/2014.</CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>FPSO</Label>
                  <Select value={formData.fpso_name} onValueChange={(v) => setFormData({ ...formData, fpso_name: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="FPSO SEPETIBA">FPSO SEPETIBA</SelectItem>
                      <SelectItem value="FPSO SAQUAREMA">FPSO SAQUAREMA</SelectItem>
                      <SelectItem value="FPSO MARICÁ">FPSO MARICÁ</SelectItem>
                      <SelectItem value="FPSO PARATY">FPSO PARATY</SelectItem>
                      <SelectItem value="FPSO ILHABELA">FPSO ILHABELA</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Equipment Tag / Ponto de Medição</Label>
                  <Input value={formData.tag} onChange={(e) => setFormData({ ...formData, tag: e.target.value })} placeholder="e.g. 62-FT-1101" />
                </div>
                <div className="space-y-2">
                  <Label>Failure Frequency / Date</Label>
                  <Input type="datetime-local" value={formData.failure_date} onChange={(e) => setFormData({ ...formData, failure_date: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>ANP Classification</Label>
                  <Select value={formData.anp_classification} onValueChange={(v) => setFormData({ ...formData, anp_classification: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Crítica">Crítica</SelectItem>
                      <SelectItem value="Grave">Grave</SelectItem>
                      <SelectItem value="Tolerável">Tolerável</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Estimated Volume Impact (m³)</Label>
                  <Input type="number" value={formData.estimated_volume_impact} onChange={(e) => setFormData({ ...formData, estimated_volume_impact: Number(e.target.value) })} />
                </div>
                <div className="space-y-2">
                  <Label>Impact Level</Label>
                  <Select value={formData.impact} onValueChange={(v) => setFormData({ ...formData, impact: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="High">High Impact</SelectItem>
                      <SelectItem value="Medium">Medium Impact</SelectItem>
                      <SelectItem value="Low">Low Impact</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Description of Failure (Natureza da Falha)</Label>
                <Textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={3} />
              </div>

              <div className="space-y-2">
                <Label>Initial Corrective Actions (Providências Adotadas)</Label>
                <Textarea value={formData.corrective_action} onChange={(e) => setFormData({ ...formData, corrective_action: e.target.value })} rows={3} />
              </div>
            </CardContent>
            <CardFooter className="bg-slate-50 rounded-b-lg justify-end gap-3 p-4">
              <Button variant="outline" onClick={() => setActiveTab("list")}>Cancel</Button>
              <Button className="bg-[#FF6B35] hover:bg-[#e85a20] text-white" onClick={handleCreate}>Save as Draft</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="config" className="mt-4">
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="border-none shadow-sm ring-1 ring-slate-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Mail className="h-5 w-5 text-[#003D5C]" /> Automatic Distribution</CardTitle>
                <CardDescription>Setup emails to receive approved reports automatically.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Select value={newEmail.fpso} onValueChange={(v) => setNewEmail({ ...newEmail, fpso: v })}>
                    <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="FPSO SEPETIBA">SEPETIBA</SelectItem>
                      <SelectItem value="FPSO SAQUAREMA">SAQUAREMA</SelectItem>
                      <SelectItem value="FPSO MARICÁ">MARICÁ</SelectItem>
                      <SelectItem value="FPSO PARATY">PARATY</SelectItem>
                      <SelectItem value="FPSO ILHABELA">ILHABELA</SelectItem>
                    </SelectContent>
                  </Select>
                  <Input placeholder="email@company.com" value={newEmail.email} onChange={(e) => setNewEmail({ ...newEmail, email: e.target.value })} />
                  <Button size="icon" onClick={handleAddEmail}><Plus className="h-4 w-4" /></Button>
                </div>

                <div className="space-y-2 pt-4">
                  {emailLists.map((rec) => (
                    <div key={rec.id} className="flex items-center justify-between p-2 bg-slate-50 rounded text-sm">
                      <div className="flex flex-col">
                        <span className="font-bold text-[#003D5C]">{rec.fpso_name}</span>
                        <span className="text-slate-500">{rec.email}</span>
                      </div>
                      <Badge variant="outline" className="text-xs text-green-600 bg-green-50 border-green-100">Active</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-blue-50/50 border-blue-100 shadow-none ring-1 ring-blue-100">
              <CardHeader>
                <CardTitle className="text-blue-900 text-base">Regulatory Note</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-blue-800 space-y-2">
                <p>According to <strong>ANP Resolution 18/2014</strong>, failures must be reported within 24 hours (Initial) and closed within 30 days (Final).</p>
                <p>Approving a report in this module triggers a legal distribution of the PDF/Excel summary to all registered authorities and internal stakeholders.</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
