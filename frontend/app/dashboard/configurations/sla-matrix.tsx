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

export function SlaMatrix() {
  const [rules, setRules] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [formData, setFormData] = useState({
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
  })

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
      const res = await apiFetch("/config/sla-rules", {
        method: "POST",
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        toast.success("SLA Rule added/updated")
        setOpen(false)
        loadRules()
      } else {
        toast.error("Failed to save SLA Rule")
      }
    } catch (error) {
      toast.error("Failed to save SLA Rule")
    }
  }

  const getStatusBadge = (sv: string) => {
    if (sv === "Approved") return <Badge className="bg-emerald-600 text-white">Approved</Badge>
    if (sv === "Reproved") return <Badge className="bg-red-600 text-white">Reproved</Badge>
    return <Badge variant="secondary">Any</Badge>
  }

  if (loading) return <div>Loading SLA matrix...</div>

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>SLA Matrix (All 22 Periodic Analyses)</CardTitle>
          <CardDescription>
            Configure intervals and deadlines for periodic analyses. Rows with &quot;Approved&quot; or &quot;Reproved&quot; apply only when validation produces that outcome.
          </CardDescription>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Add SLA Rule</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Add / Edit SLA Rule</DialogTitle>
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
                  />
                </div>
                <div className="space-y-2">
                  <Label>Analysis Type</Label>
                  <Input
                    required
                    value={formData.analysis_type}
                    onChange={(e) => setFormData({ ...formData, analysis_type: e.target.value })}
                    placeholder="e.g. Chromatography"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Local</Label>
                  <Select
                    value={formData.local}
                    onValueChange={(v) => setFormData({ ...formData, local: v })}
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
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Any">Any (No validation)</SelectItem>
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
                    placeholder="Frequency"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Disembark (Days)</Label>
                  <Input
                    type="number"
                    value={formData.disembark_days}
                    onChange={(e) => setFormData({ ...formData, disembark_days: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Lab (Days)</Label>
                  <Input
                    type="number"
                    value={formData.lab_days}
                    onChange={(e) => setFormData({ ...formData, lab_days: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Report (Days)</Label>
                  <Input
                    type="number"
                    value={formData.report_days}
                    onChange={(e) => setFormData({ ...formData, report_days: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Flow Computer (Days)</Label>
                  <Input
                    type="number"
                    value={formData.fc_days}
                    onChange={(e) => setFormData({ ...formData, fc_days: e.target.value })}
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
              <div className="flex items-center space-x-2 pt-2">
                <Switch
                  checked={formData.fc_is_business_days}
                  onCheckedChange={(checked) => setFormData({ ...formData, fc_is_business_days: checked })}
                />
                <Label>FC Days are Business Days</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  checked={formData.needs_validation}
                  onCheckedChange={(checked) => setFormData({ ...formData, needs_validation: checked })}
                />
                <Label>Requires Automated Validation</Label>
              </div>
              <div className="flex justify-end pt-4">
                <Button type="submit">Save</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Classification</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Local</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Freq. (Days)</TableHead>
              <TableHead>Disembark</TableHead>
              <TableHead>Lab</TableHead>
              <TableHead>Report</TableHead>
              <TableHead>FC Update</TableHead>
              <TableHead>Reschedule</TableHead>
              <TableHead>Validation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rules.map((rule) => (
              <TableRow key={rule.id}>
                <TableCell className="font-medium">{rule.classification}</TableCell>
                <TableCell>{rule.analysis_type}</TableCell>
                <TableCell>{rule.local}</TableCell>
                <TableCell>{getStatusBadge(rule.status_variation || "Any")}</TableCell>
                <TableCell>{rule.interval_days || "-"}</TableCell>
                <TableCell>{rule.disembark_days || "-"}</TableCell>
                <TableCell>{rule.lab_days || "-"}</TableCell>
                <TableCell>{rule.report_days || "-"}</TableCell>
                <TableCell>
                  {rule.fc_days || "-"} {rule.fc_is_business_days && rule.fc_days ? "(B.D.)" : ""}
                </TableCell>
                <TableCell>
                  {rule.reproval_reschedule_days ? `${rule.reproval_reschedule_days} B.D.` : "-"}
                </TableCell>
                <TableCell>{rule.needs_validation ? "Yes" : "No"}</TableCell>
              </TableRow>
            ))}
            {rules.length === 0 && (
              <TableRow>
                <TableCell colSpan={11} className="text-center py-4 text-muted-foreground">
                  No SLA rules configured. The system will use the default static matrix.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
