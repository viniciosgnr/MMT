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
  Bell,
  AlertTriangle,
  Check,
  Settings,
  Plus,
  Filter,
  RefreshCcw,
  ExternalLink,
  Info,
  User,
  Clock,
  MessageSquare
} from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { toast } from "sonner"
import { format } from "date-fns"
import { apiFetch } from "@/lib/api"

// Types
type Alert = {
  id: number
  type: string
  severity: "Info" | "Warning" | "Critical"
  title: string
  message: string
  fpso_name: string
  tag_number?: string
  created_at: string
  acknowledged: number
  acknowledged_by?: string
  acknowledged_at?: string
  justification?: string
  linked_event_type?: string
  linked_event_id?: number
  run_recheck: number
  run_recheck: number
}

import { AuditPanel } from "./audit-panel"
import { FCVerificationPanel } from "./fc-verification-panel"

export default function MonitoringPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState("active")
  const [filterFPSO, setFilterFPSO] = useState("all")

  // Acknowledgment State
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [isAckDialogOpen, setIsAckDialogOpen] = useState(false)
  const [ackJustification, setAckJustification] = useState("")
  const [linkedEventType, setLinkedEventType] = useState("None")
  const [linkedEventId, setLinkedEventId] = useState("")
  const [runRecheck, setRunRecheck] = useState(true)

  // Configuration State
  const [configs, setConfigs] = useState<any[]>([])
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false)
  const [newConfig, setNewConfig] = useState({
    fpso_name: "FPSO MARICÁ",
    alert_type: "System Configuration",
    notify_email: true,
    notify_whatsapp: false,
    notify_in_app: true,
    recipients: [{ user_name: "", email: "", whatsapp_number: "", receive_in_app: true }]
  })

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      let url = "/alerts"
      const params = new URLSearchParams()
      if (filterStatus === "active") params.append("acknowledged", "false")
      if (filterStatus === "history") params.append("acknowledged", "true")
      if (filterFPSO !== "all") params.append("fpso_name", filterFPSO)

      if (params.toString()) url += `?${params.toString()}`

      const response = await apiFetch(url)
      if (response.ok) {
        setAlerts(await response.json())
      } else {
        toast.error("Failed to load alerts")
      }
    } catch (error) {
      console.error("Failed to fetch alerts", error)
      toast.error("Failed to load alerts")
    } finally {
      setLoading(false)
    }
  }

  const fetchConfigs = async () => {
    try {
      const response = await apiFetch("/alerts/configs")
      if (response.ok) {
        setConfigs(await response.json())
      }
    } catch (error) {
      console.error("Failed to fetch configs", error)
    }
  }

  useEffect(() => {
    if (filterStatus === "configuration") {
      fetchConfigs()
    } else {
      fetchAlerts()
    }
  }, [filterStatus, filterFPSO])

  const handleAcknowledge = async () => {
    if (!selectedAlert) return
    try {
      const response = await apiFetch(`/alerts/${selectedAlert.id}/acknowledge`, {
        method: "PUT",
        body: JSON.stringify({
          acknowledged_by: "Current User", // In a real app, this would be the logged-in user
          justification: ackJustification,
          linked_event_type: linkedEventType === "None" ? null : linkedEventType,
          linked_event_id: linkedEventId ? parseInt(linkedEventId) : null,
          run_recheck: runRecheck
        })
      })

      if (response.ok) {
        toast.success("Alert acknowledged successfully")
        setIsAckDialogOpen(false)
        setAckJustification("")
        setLinkedEventType("None")
        setLinkedEventId("")
        fetchAlerts()
      } else {
        toast.error("Failed to acknowledge alert")
      }
    } catch (error) {
      toast.error("Error acknowledging alert")
    }
  }

  const handleCreateConfig = async () => {
    try {
      const response = await apiFetch("/alerts/configs", {
        method: "POST",
        body: JSON.stringify(newConfig)
      })

      if (response.ok) {
        toast.success("Alert configuration created")
        setIsConfigDialogOpen(false)
        fetchConfigs()
        setNewConfig({
          fpso_name: "FPSO MARICÁ",
          alert_type: "System Configuration",
          notify_email: true,
          notify_whatsapp: false,
          notify_in_app: true,
          recipients: [{ user_name: "", email: "", whatsapp_number: "", receive_in_app: true }]
        })
      } else {
        toast.error("Failed to create configuration")
      }
    } catch (error) {
      toast.error("Error creating configuration")
    }
  }

  const addRecipient = () => {
    setNewConfig({
      ...newConfig,
      recipients: [...newConfig.recipients, { user_name: "", email: "", whatsapp_number: "", receive_in_app: true }]
    })
  }

  const updateRecipient = (index: number, field: string, value: any) => {
    const updated = [...newConfig.recipients]
    updated[index] = { ...updated[index], [field]: value }
    setNewConfig({ ...newConfig, recipients: updated })
  }

  const removeRecipient = (index: number) => {
    if (newConfig.recipients.length === 1) return
    const updated = newConfig.recipients.filter((_, i) => i !== index)
    setNewConfig({ ...newConfig, recipients: updated })
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "Critical":
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-100 border-red-200 font-black text-[10px] uppercase tracking-widest px-3 py-1">Critical</Badge>
      case "Warning":
        return <Badge className="bg-amber-50 text-amber-700 hover:bg-amber-100 border-amber-200 font-black text-[10px] uppercase tracking-widest px-3 py-1">Warning</Badge>
      default:
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200 font-black text-[10px] uppercase tracking-widest px-3 py-1">Info</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#003D5C]">Monitoring & Alerts (M6)</h1>
          <p className="text-muted-foreground text-sm font-medium">System verification, compliance checks, and real-time notifications.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchAlerts} disabled={loading}>
            <RefreshCcw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} /> Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-[#003D5C] text-white shadow-lg">
          <CardHeader className="pb-2">
            <CardTitle className="text-[10px] font-bold uppercase tracking-widest text-white/50">Total Unread</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-black">{alerts.filter(a => !a.acknowledged).length}</div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-red-500 shadow-md">
          <CardHeader className="pb-2">
            <CardTitle className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Critical</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-black text-red-600">{alerts.filter(a => a.severity === "Critical").length}</div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500 shadow-md">
          <CardHeader className="pb-2">
            <CardTitle className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-black text-amber-500">{alerts.filter(a => a.severity === "Warning").length}</div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-500 shadow-md">
          <CardHeader className="pb-2">
            <CardTitle className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Info</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-black text-blue-500">{alerts.filter(a => a.severity === "Info").length}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="active" className="w-full" onValueChange={setFilterStatus}>
        <div className="flex items-center justify-between border-b pb-1">
          <TabsList className="bg-transparent h-auto p-0 gap-6">
            <TabsTrigger value="active" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#FF6B35] data-[state=active]:bg-transparent data-[state=active]:shadow-none text-[#003D5C] font-bold px-0 pb-2">Active Alerts</TabsTrigger>
            <TabsTrigger value="history" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#FF6B35] data-[state=active]:bg-transparent data-[state=active]:shadow-none text-[#003D5C] font-bold px-0 pb-2">History & Audit</TabsTrigger>
            <TabsTrigger value="audit" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#FF6B35] data-[state=active]:bg-transparent data-[state=active]:shadow-none text-[#003D5C] font-bold px-0 pb-2">Audit (6.8)</TabsTrigger>
            <TabsTrigger value="fc-verification" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#FF6B35] data-[state=active]:bg-transparent data-[state=active]:shadow-none text-[#003D5C] font-bold px-0 pb-2">FC Config Check (6.8)</TabsTrigger>
            <TabsTrigger value="configuration" className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#FF6B35] data-[state=active]:bg-transparent data-[state=active]:shadow-none text-[#003D5C] font-bold px-0 pb-2">Configuration (6.2)</TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-3 mb-2">
            <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-md px-3 py-1.5 text-xs shadow-sm">
              <Filter className="h-3 w-3 text-slate-400" />
              <span className="font-bold text-slate-500 uppercase tracking-tighter">FPSO Context:</span>
              <Select value={filterFPSO} onValueChange={setFilterFPSO}>
                <SelectTrigger className="h-6 w-[160px] border-none shadow-none p-0 text-[#003D5C] font-black focus:ring-0">
                  <SelectValue placeholder="All Units" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Units</SelectItem>
                  <SelectItem value="FPSO SEPETIBA">FPSO SEPETIBA</SelectItem>
                  <SelectItem value="FPSO SAQUAREMA">FPSO SAQUAREMA</SelectItem>
                  <SelectItem value="FPSO MARICÁ">FPSO MARICÁ</SelectItem>
                  <SelectItem value="FPSO PARATY">FPSO PARATY</SelectItem>
                  <SelectItem value="FPSO ILHABELA">FPSO ILHABELA</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <TabsContent value="active" className="space-y-4 mt-6">
          <Card className="shadow-sm border-slate-200">
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-slate-50/80">
                  <TableRow>
                    <TableHead className="w-[120px] text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Severity</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Details</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Asset / Tag</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Detection Time</TableHead>
                    <TableHead className="text-right text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Workflow</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-32 text-center text-slate-400">
                        <div className="flex flex-col items-center gap-2">
                          <RefreshCcw className="h-8 w-8 animate-spin text-slate-200" />
                          <span className="font-medium">Refreshing alert stream...</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : alerts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-32 text-center text-slate-400 font-medium italic">
                        <Bell className="h-8 w-8 mx-auto mb-2 opacity-20" />
                        No active alerts requiring attention.
                      </TableCell>
                    </TableRow>
                  ) : (
                    alerts.map((alert) => (
                      <TableRow key={alert.id} className="hover:bg-[#F8FAFC] transition-colors group">
                        <TableCell>{getSeverityBadge(alert.severity)}</TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-black text-sm text-[#003D5C] group-hover:text-[#FF6B35] transition-colors">{alert.title}</span>
                            <span className="text-xs text-slate-500 line-clamp-1 font-medium">{alert.message}</span>
                            <div className="flex gap-2 mt-1.5">
                              <Badge className="text-[9px] bg-slate-100 text-[#003D5C] hover:bg-slate-200 border-none font-black uppercase tracking-tighter">{alert.type}</Badge>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="text-xs font-black text-slate-700">{alert.fpso_name}</span>
                            <span className="text-[10px] text-[#FF6B35] font-black group-hover:underline underline-offset-2">{alert.tag_number || "SYSTEM"}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-xs text-slate-500">
                          <div className="flex items-center gap-1.5 font-black text-[#003D5C]/60">
                            <Clock className="h-3 w-3" />
                            {alert.created_at ? format(new Date(alert.created_at), "dd/MM/yyyy HH:mm") : "-"}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            className="bg-[#003D5C] hover:bg-[#FF6B35] text-white text-[10px] font-black h-8 px-4 rounded-full shadow-sm hover:shadow-md transition-all uppercase tracking-widest"
                            onClick={() => {
                              setSelectedAlert(alert)
                              setIsAckDialogOpen(true)
                            }}
                          >
                            <Check className="mr-1.5 h-3 w-3" /> Acknowledge
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4 mt-6">
          <Card className="shadow-sm border-slate-200">
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-slate-50/80">
                  <TableRow>
                    <TableHead className="w-[120px] text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Severity</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Alert Summary</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Acknowledgment Details</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Audit Trail Link</TableHead>
                    <TableHead className="text-right text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-32 text-center text-slate-400">Loading audit log...</TableCell>
                    </TableRow>
                  ) : alerts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="h-32 text-center text-slate-400 font-medium italic">No historical alerts found.</TableCell>
                    </TableRow>
                  ) : (
                    alerts.map((alert) => (
                      <TableRow key={alert.id} className="hover:bg-slate-50/50 transition-colors">
                        <TableCell>{getSeverityBadge(alert.severity)}</TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-black text-sm text-[#003D5C]">{alert.title}</span>
                            <span className="text-[10px] text-slate-400 uppercase font-black tracking-tighter">{alert.fpso_name}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1.5">
                            <div className="flex items-center gap-1.5 text-xs text-slate-700 font-black">
                              <div className="h-5 w-5 rounded-full bg-slate-100 flex items-center justify-center">
                                <User className="h-3 w-3 text-slate-500" />
                              </div>
                              {alert.acknowledged_by}
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-black">
                              <Check className="h-3 w-3 text-emerald-500" />
                              {alert.acknowledged_at ? format(new Date(alert.acknowledged_at), "dd/MM/yyyy HH:mm") : "-"}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {alert.linked_event_type ? (
                            <Badge variant="outline" className="text-[9px] border-amber-200 bg-amber-50 text-amber-700 font-black uppercase tracking-tighter cursor-pointer hover:bg-amber-100 transition-colors">
                              <ExternalLink className="h-2 w-2 mr-1" />
                              {alert.linked_event_type} #{alert.linked_event_id}
                            </Badge>
                          ) : (
                            <span className="text-[10px] text-slate-300 italic font-bold">No linked events</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" className="h-8 text-[#003D5C] font-black hover:bg-slate-100 rounded-full">
                            <Info className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="configuration" className="mt-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-black text-[#003D5C]">Alert Recipient Lists</h3>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Configure who receives notifications per FPSO and Category</p>
            </div>
            <Button className="bg-[#003D5C] hover:bg-[#FF6B35] text-white font-black text-xs uppercase tracking-widest rounded-full px-6 shadow-md" onClick={() => setIsConfigDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" /> Create New Config (6.2)
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {configs.length === 0 ? (
              <Card className="border-dashed border-2 border-slate-200 bg-slate-50">
                <CardContent className="flex flex-col items-center justify-center py-12 text-slate-400">
                  <Settings className="h-12 w-12 mb-4 opacity-10" />
                  <p className="font-bold">No custom alert rules configured yet.</p>
                </CardContent>
              </Card>
            ) : (
              <Card className="shadow-sm overflow-hidden">
                <Table>
                  <TableHeader className="bg-slate-50">
                    <TableRow>
                      <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">FPSO Target</TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Alert Category</TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Active Channels</TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Authorized Recipients</TableHead>
                      <TableHead className="text-right text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Manage</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {configs.map((config) => (
                      <TableRow key={config.id} className="hover:bg-slate-50/50 transition-colors">
                        <TableCell className="font-black text-xs text-[#003D5C]">{config.fpso_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-[10px] font-black border-slate-200 bg-white text-[#003D5C]">{config.alert_type}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1.5">
                            {config.notify_email ? <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50 text-[9px] border-none font-black uppercase tracking-tighter">Email</Badge> : null}
                            {config.notify_whatsapp ? <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50 text-[9px] border-none font-black uppercase tracking-tighter">WhatsApp</Badge> : null}
                            {config.notify_in_app ? <Badge className="bg-amber-50 text-amber-700 hover:bg-amber-50 text-[9px] border-none font-black uppercase tracking-tighter">In-App</Badge> : null}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex -space-x-2">
                            {config.recipients.map((r: any, i: number) => (
                              <div key={i} className="h-6 w-6 rounded-full border-2 border-white bg-[#003D5C] flex items-center justify-center" title={r.user_name}>
                                <span className="text-[8px] text-white font-bold">{r.user_name.charAt(0)}</span>
                              </div>
                            ))}
                            {config.recipients.length > 3 && (
                              <div className="h-6 w-6 rounded-full border-2 border-white bg-slate-100 flex items-center justify-center">
                                <span className="text-[8px] text-slate-500 font-bold">+{config.recipients.length - 3}</span>
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" className="h-8 rounded-full hover:bg-[#FF6B35] hover:text-white transition-all">
                            <Settings className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            )}
          </div>
        </TabsContent>


        <TabsContent value="audit" className="mt-6">
          <AuditPanel />
        </TabsContent>

        <TabsContent value="fc-verification" className="mt-6">
          <FCVerificationPanel />
        </TabsContent>

      </Tabs>

      {/* Acknowledge Dialog */}
      <Dialog open={isAckDialogOpen} onOpenChange={setIsAckDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-[#003D5C] font-black text-xl flex items-center gap-2">
              <Check className="h-5 w-5 text-emerald-500" /> Acknowledge Alert
            </DialogTitle>
            <DialogDescription className="text-xs font-bold text-slate-400 uppercase tracking-widest">Provide justification and link to operational events</DialogDescription>
          </DialogHeader>

          {selectedAlert && (
            <div className="py-4 space-y-4">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-black text-[#003D5C] uppercase tracking-tighter">{selectedAlert.fpso_name}</span>
                  {getSeverityBadge(selectedAlert.severity)}
                </div>
                <h4 className="font-black text-sm text-[#003D5C]">{selectedAlert.title}</h4>
                <p className="text-xs text-slate-500 mt-1">{selectedAlert.message}</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="justification" className="text-[10px] font-black uppercase tracking-widest text-slate-500 font-bold">Justification</Label>
                <Textarea
                  id="justification"
                  placeholder="Describe the action taken or reason for acknowledgment..."
                  className="min-h-[100px] text-xs font-medium"
                  value={ackJustification}
                  onChange={(e) => setAckJustification(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500 font-bold">Linked Event</Label>
                  <Select value={linkedEventType} onValueChange={setLinkedEventType}>
                    <SelectTrigger className="font-bold text-xs text-[#003D5C]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="None">None</SelectItem>
                      <SelectItem value="Failure Notification">Failure Notification</SelectItem>
                      <SelectItem value="Equipment Replacement">Equipment Replacement</SelectItem>
                      <SelectItem value="Maintenance Order">Maintenance Order</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500 font-bold">Event ID</Label>
                  <Input
                    placeholder="e.g. 12345"
                    className="font-bold text-xs text-[#003D5C]"
                    value={linkedEventId}
                    onChange={(e) => setLinkedEventId(e.target.value)}
                    disabled={linkedEventType === "None"}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <Checkbox id="recheck" checked={runRecheck} onCheckedChange={(v) => setRunRecheck(!!v)} />
                <label htmlFor="recheck" className="text-xs font-bold text-[#003D5C] cursor-pointer">Run compliance re-check immediately</label>
              </div>
            </div>
          )}

          <DialogFooter className="bg-slate-50 -mx-6 -mb-6 p-6 mt-4">
            <Button variant="ghost" className="text-xs font-black uppercase tracking-widest" onClick={() => setIsAckDialogOpen(false)}>Cancel</Button>
            <Button
              className="bg-[#003D5C] hover:bg-[#FF6B35] text-white font-black text-xs uppercase tracking-widest rounded-full px-8 shadow-md"
              onClick={handleAcknowledge}
              disabled={!ackJustification}
            >
              Confirm Acknowledgment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Configuration Dialog */}
      <Dialog open={isConfigDialogOpen} onOpenChange={setIsConfigDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-[#003D5C] font-black text-xl flex items-center gap-2">
              <Settings className="h-5 w-5" /> New Alert Configuration
            </DialogTitle>
            <DialogDescription className="text-xs font-bold text-slate-400 uppercase tracking-widest">Define notification logic and recipient groups</DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-2 gap-6 py-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500">FPSO Target</Label>
                <Select value={newConfig.fpso_name} onValueChange={(v) => setNewConfig({ ...newConfig, fpso_name: v })}>
                  <SelectTrigger className="font-black text-xs text-[#003D5C]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FPSO SEPETIBA">FPSO SEPETIBA</SelectItem>
                    <SelectItem value="FPSO SAQUAREMA">FPSO SAQUAREMA</SelectItem>
                    <SelectItem value="FPSO MARICÁ">FPSO MARICÁ</SelectItem>
                    <SelectItem value="FPSO PARATY">FPSO PARATY</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Alert Category</Label>
                <Select value={newConfig.alert_type} onValueChange={(v) => setNewConfig({ ...newConfig, alert_type: v })}>
                  <SelectTrigger className="font-black text-xs text-[#003D5C]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="System Configuration">System Configuration</SelectItem>
                    <SelectItem value="Metrological Confirmation">Metrological Confirmation</SelectItem>
                    <SelectItem value="Sampling">Sampling Compliance</SelectItem>
                    <SelectItem value="Failure Notification">Failure Deadlines</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-4 bg-slate-50 p-4 rounded-lg border border-slate-100">
                <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Notification Channels</Label>
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-notif" className="text-xs font-bold text-[#003D5C]">Email Notification</Label>
                    <Checkbox id="email-notif" checked={newConfig.notify_email} onCheckedChange={(v) => setNewConfig({ ...newConfig, notify_email: !!v })} />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="wa-notif" className="text-xs font-bold text-[#003D5C]">WhatsApp Notification</Label>
                    <Checkbox id="wa-notif" checked={newConfig.notify_whatsapp} onCheckedChange={(v) => setNewConfig({ ...newConfig, notify_whatsapp: !!v })} />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="app-notif" className="text-xs font-bold text-[#003D5C]">In-App Dashboard</Label>
                    <Checkbox id="app-notif" checked={newConfig.notify_in_app} onCheckedChange={(v) => setNewConfig({ ...newConfig, notify_in_app: !!v })} />
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Recipients List</Label>
                <Button variant="outline" size="sm" className="h-6 text-[9px] font-black uppercase tracking-tighter" onClick={addRecipient}>
                  <Plus className="h-3 w-3 mr-1" /> Add Recipient
                </Button>
              </div>

              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                {newConfig.recipients.map((recipient, idx) => (
                  <div key={idx} className="p-3 bg-white border rounded-md shadow-sm space-y-2 relative group">
                    <Button
                      variant="ghost" size="icon"
                      className="absolute -top-2 -right-2 h-5 w-5 rounded-full bg-red-100 text-red-600 hover:bg-red-600 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => removeRecipient(idx)}
                    >
                      ×
                    </Button>
                    <Input
                      placeholder="User Name"
                      className="h-8 text-[11px] font-bold"
                      value={recipient.user_name}
                      onChange={(e) => updateRecipient(idx, "user_name", e.target.value)}
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <Input
                        placeholder="Email Address"
                        className="h-8 text-[10px]"
                        value={recipient.email}
                        onChange={(e) => updateRecipient(idx, "email", e.target.value)}
                      />
                      <Input
                        placeholder="WhatsApp (optional)"
                        className="h-8 text-[10px]"
                        value={recipient.whatsapp_number}
                        onChange={(e) => updateRecipient(idx, "whatsapp_number", e.target.value)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter className="bg-slate-50 -mx-6 -mb-6 p-6 mt-4">
            <Button variant="ghost" className="text-xs font-black uppercase tracking-widest" onClick={() => setIsConfigDialogOpen(false)}>Cancel</Button>
            <Button
              className="bg-[#003D5C] hover:bg-[#FF6B35] text-white font-black text-xs uppercase tracking-widest rounded-full px-8"
              onClick={handleCreateConfig}
              disabled={newConfig.recipients.some(r => !r.user_name)}
            >
              Initialize Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div >
  )
}

function cn(...classes: any[]) {
  return classes.filter(Boolean).join(" ")
}

