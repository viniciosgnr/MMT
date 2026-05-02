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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

export function SlaMatrix() {
  const [rules, setRules] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [formData, setFormData] = useState({
    classification: "",
    analysis_type: "",
    local: "Onshore",
    interval_days: "",
    disembark_days: "",
    lab_days: "",
    report_days: "",
    fc_days: "",
    fc_is_business_days: false,
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
        interval_days: formData.interval_days ? parseInt(formData.interval_days) : null,
        disembark_days: formData.disembark_days ? parseInt(formData.disembark_days) : null,
        lab_days: formData.lab_days ? parseInt(formData.lab_days) : null,
        report_days: formData.report_days ? parseInt(formData.report_days) : null,
        fc_days: formData.fc_days ? parseInt(formData.fc_days) : null,
        fc_is_business_days: formData.fc_is_business_days,
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

  if (loading) return <div>Loading SLA matrix...</div>

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>SLA Matrix (Analysis Limits)</CardTitle>
          <CardDescription>
            Configure intervals and deadlines for periodic analyses based on classification and type.
          </CardDescription>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>Add SLA Rule</Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
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
                  <Input
                    required
                    value={formData.local}
                    onChange={(e) => setFormData({ ...formData, local: e.target.value })}
                    placeholder="Onshore/Offshore"
                  />
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
              <TableHead>Freq. (Days)</TableHead>
              <TableHead>Disembark</TableHead>
              <TableHead>Lab</TableHead>
              <TableHead>Report</TableHead>
              <TableHead>FC Update</TableHead>
              <TableHead>Validation</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rules.map((rule) => (
              <TableRow key={rule.id}>
                <TableCell className="font-medium">{rule.classification}</TableCell>
                <TableCell>{rule.analysis_type}</TableCell>
                <TableCell>{rule.local}</TableCell>
                <TableCell>{rule.interval_days || "-"}</TableCell>
                <TableCell>{rule.disembark_days || "-"}</TableCell>
                <TableCell>{rule.lab_days || "-"}</TableCell>
                <TableCell>{rule.report_days || "-"}</TableCell>
                <TableCell>
                  {rule.fc_days || "-"} {rule.fc_is_business_days && rule.fc_days ? "(B.D.)" : ""}
                </TableCell>
                <TableCell>{rule.needs_validation ? "Yes" : "No"}</TableCell>
              </TableRow>
            ))}
            {rules.length === 0 && (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-4 text-muted-foreground">
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
