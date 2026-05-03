"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface SLARuleData {
  id: number
  classification: string
  analysis_type: string
  local: string
  status_variation: string
  interval_days: number | null
  disembark_days: number | null
  lab_days: number | null
  report_days: number | null
  fc_days: number | null
  fc_is_business_days: boolean
  reproval_reschedule_days: number | null
  needs_validation: boolean
  created_at: string
}

const emptyForm = {
  classification: "",
  analysis_type: "",
  local: "Onshore",
  status_variation: "Any",
  interval_days: "",
  disembark_days: "",
  lab_days: "",
  report_days: "",
  fc_days: "",
  fc_is_business_days: false,
  reproval_reschedule_days: "",
  needs_validation: true,
}

export function SlaMatrix() {
  const [rules, setRules] = useState<SLARuleData[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<SLARuleData | null>(null)
  const [formData, setFormData] = useState({ ...emptyForm })

  const loadRules = async () => {
    try {
      const res = await apiFetch("/config/sla-rules")
      if (res.ok) {
        setRules(await res.json())
      }
    } catch (error) {
      toast.error("Failed to load SLA rules")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRules()
  }, [])

  const openCreateDialog = () => {
    setEditingRule(null)
    setFormData({ ...emptyForm })
    setOpen(true)
  }

  const openEditDialog = (rule: SLARuleData) => {
    setEditingRule(rule)
    setFormData({
      classification: rule.classification,
      analysis_type: rule.analysis_type,
      local: rule.local,
      status_variation: rule.status_variation || "Any",
      interval_days: rule.interval_days?.toString() || "",
      disembark_days: rule.disembark_days?.toString() || "",
      lab_days: rule.lab_days?.toString() || "",
      report_days: rule.report_days?.toString() || "",
      fc_days: rule.fc_days?.toString() || "",
      fc_is_business_days: rule.fc_is_business_days || false,
      reproval_reschedule_days: rule.reproval_reschedule_days?.toString() || "",
      needs_validation: rule.needs_validation ?? true,
    })
    setOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const payload = {
        classification: formData.classification,
        analysis_type: formData.analysis_type,
        local: formData.local,
        status_variation: formData.status_variation,
        interval_days: formData.interval_days ? parseInt(formData.interval_days) : null,
        disembark_days: formData.disembark_days ? parseInt(formData.disembark_days) : null,
        lab_days: formData.lab_days ? parseInt(formData.lab_days) : null,
        report_days: formData.report_days ? parseInt(formData.report_days) : null,
        fc_days: formData.fc_days ? parseInt(formData.fc_days) : null,
        fc_is_business_days: formData.fc_is_business_days,
        reproval_reschedule_days: formData.reproval_reschedule_days ? parseInt(formData.reproval_reschedule_days) : null,
        needs_validation: formData.needs_validation,
      }

      let res: Response
      if (editingRule) {
        // PUT update
        res = await apiFetch(`/config/sla-rules/${editingRule.id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        })
      } else {
        // POST create
        res = await apiFetch("/config/sla-rules", {
          method: "POST",
          body: JSON.stringify(payload),
        })
      }

      if (res.ok) {
        toast.success(editingRule ? "SLA Rule updated" : "SLA Rule created")
        setOpen(false)
        setEditingRule(null)
        loadRules()
      } else {
        const err = await res.text()
        toast.error(`Failed to save SLA Rule: ${err}`)
      }
    } catch (error) {
      toast.error("Failed to save SLA Rule")
    }
  }

  const handleDelete = async (rule: SLARuleData) => {
    if (!confirm(`Delete rule: ${rule.classification} / ${rule.analysis_type} / ${rule.local} / ${rule.status_variation}?`)) return
    try {
      const res = await apiFetch(`/config/sla-rules/${rule.id}`, { method: "DELETE" })
      if (res.ok) {
        toast.success("SLA Rule deleted")
        loadRules()
      } else {
        toast.error("Failed to delete SLA Rule")
      }
    } catch (error) {
      toast.error("Failed to delete SLA Rule")
    }
  }

  const getStatusBadge = (sv: string) => {
    if (sv === "Approved") return <Badge className="bg-emerald-600 text-white">Approved</Badge>
    if (sv === "Reproved") return <Badge className="bg-red-600 text-white">Reproved</Badge>
    return <Badge variant="secondary">Any</Badge>
  }

  if (loading) return <div className="flex items-center justify-center p-8">Loading SLA matrix...</div>

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>SLA Matrix — All {rules.length} Periodic Analyses</CardTitle>
          <CardDescription>
            Click on any row to edit deadlines. Rows with &quot;Approved&quot; or &quot;Reproved&quot; apply only when validation produces that outcome.
          </CardDescription>
        </div>
        <Button onClick={openCreateDialog}>+ Add Rule</Button>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="font-semibold">Classification</TableHead>
                <TableHead className="font-semibold">Type</TableHead>
                <TableHead className="font-semibold">Local</TableHead>
                <TableHead className="font-semibold">Status</TableHead>
                <TableHead className="font-semibold text-center">Interval</TableHead>
                <TableHead className="font-semibold text-center">Disembark</TableHead>
                <TableHead className="font-semibold text-center">Lab</TableHead>
                <TableHead className="font-semibold text-center">Report</TableHead>
                <TableHead className="font-semibold text-center">FC Update</TableHead>
                <TableHead className="font-semibold text-center">Reschedule</TableHead>
                <TableHead className="font-semibold text-center">Validation</TableHead>
                <TableHead className="font-semibold text-center">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rules.map((rule) => (
                <TableRow
                  key={rule.id}
                  className="cursor-pointer hover:bg-muted/30 transition-colors"
                  onClick={() => openEditDialog(rule)}
                >
                  <TableCell className="font-medium">{rule.classification}</TableCell>
                  <TableCell>{rule.analysis_type}</TableCell>
                  <TableCell>{rule.local}</TableCell>
                  <TableCell>{getStatusBadge(rule.status_variation || "Any")}</TableCell>
                  <TableCell className="text-center">{rule.interval_days ?? "-"}</TableCell>
                  <TableCell className="text-center">{rule.disembark_days ?? "-"}</TableCell>
                  <TableCell className="text-center">{rule.lab_days ?? "-"}</TableCell>
                  <TableCell className="text-center">{rule.report_days ?? "-"}</TableCell>
                  <TableCell className="text-center">
                    {rule.fc_days != null ? `${rule.fc_days}${rule.fc_is_business_days ? " B.D." : "d"}` : "-"}
                  </TableCell>
                  <TableCell className="text-center">
                    {rule.reproval_reschedule_days != null ? `${rule.reproval_reschedule_days} B.D.` : "-"}
                  </TableCell>
                  <TableCell className="text-center">
                    {rule.needs_validation ? (
                      <Badge variant="outline" className="border-green-500 text-green-600">Yes</Badge>
                    ) : (
                      <Badge variant="outline" className="border-gray-400 text-gray-500">No</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      onClick={(e) => { e.stopPropagation(); handleDelete(rule) }}
                    >
                      ✕
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {rules.length === 0 && (
                <TableRow>
                  <TableCell colSpan={12} className="text-center py-8 text-muted-foreground">
                    No SLA rules configured. Click &quot;+ Add Rule&quot; to get started.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>

      {/* Create/Edit Dialog */}
      <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) setEditingRule(null) }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingRule ? "Edit SLA Rule" : "Add SLA Rule"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Classification</Label>
                <Input
                  required
                  value={formData.classification}
                  onChange={(e) => setFormData({ ...formData, classification: e.target.value })}
                  placeholder="e.g. Fiscal"
                  disabled={!!editingRule}
                />
              </div>
              <div className="space-y-2">
                <Label>Analysis Type</Label>
                <Input
                  required
                  value={formData.analysis_type}
                  onChange={(e) => setFormData({ ...formData, analysis_type: e.target.value })}
                  placeholder="e.g. Chromatography"
                  disabled={!!editingRule}
                />
              </div>
              <div className="space-y-2">
                <Label>Local</Label>
                <Select
                  value={formData.local}
                  onValueChange={(v) => setFormData({ ...formData, local: v })}
                  disabled={!!editingRule}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Onshore">Onshore</SelectItem>
                    <SelectItem value="Offshore">Offshore</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Status Variation</Label>
                <Select
                  value={formData.status_variation}
                  onValueChange={(v) => setFormData({ ...formData, status_variation: v })}
                  disabled={!!editingRule}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Any">Any (informative)</SelectItem>
                    <SelectItem value="Approved">Approved</SelectItem>
                    <SelectItem value="Reproved">Reproved</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Interval (Days)</Label>
                <Input
                  type="number"
                  value={formData.interval_days}
                  onChange={(e) => setFormData({ ...formData, interval_days: e.target.value })}
                  placeholder="Frequency between analyses"
                />
              </div>
              <div className="space-y-2">
                <Label>Disembark (Days)</Label>
                <Input
                  type="number"
                  value={formData.disembark_days}
                  onChange={(e) => setFormData({ ...formData, disembark_days: e.target.value })}
                  placeholder="Days after collection"
                />
              </div>
              <div className="space-y-2">
                <Label>Lab (Days)</Label>
                <Input
                  type="number"
                  value={formData.lab_days}
                  onChange={(e) => setFormData({ ...formData, lab_days: e.target.value })}
                  placeholder="Days after collection"
                />
              </div>
              <div className="space-y-2">
                <Label>Report (Days)</Label>
                <Input
                  type="number"
                  value={formData.report_days}
                  onChange={(e) => setFormData({ ...formData, report_days: e.target.value })}
                  placeholder="Days after collection"
                />
              </div>
              <div className="space-y-2">
                <Label>Flow Computer (Days)</Label>
                <Input
                  type="number"
                  value={formData.fc_days}
                  onChange={(e) => setFormData({ ...formData, fc_days: e.target.value })}
                  placeholder="After report emission"
                />
              </div>
              <div className="space-y-2">
                <Label>Reproval Reschedule (B.D.)</Label>
                <Input
                  type="number"
                  value={formData.reproval_reschedule_days}
                  onChange={(e) => setFormData({ ...formData, reproval_reschedule_days: e.target.value })}
                  placeholder="e.g. 3"
                />
              </div>
            </div>
            <div className="flex items-center space-x-6 pt-2">
              <div className="flex items-center space-x-2">
                <Switch
                  id="fc-bd"
                  checked={formData.fc_is_business_days}
                  onCheckedChange={(checked) => setFormData({ ...formData, fc_is_business_days: checked })}
                />
                <Label htmlFor="fc-bd">FC Days = Business Days</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="needs-val"
                  checked={formData.needs_validation}
                  onCheckedChange={(checked) => setFormData({ ...formData, needs_validation: checked })}
                />
                <Label htmlFor="needs-val">Requires Validation</Label>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => { setOpen(false); setEditingRule(null) }}>
                Cancel
              </Button>
              <Button type="submit">
                {editingRule ? "Save Changes" : "Create Rule"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
