"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format } from "date-fns"
import { Calendar as CalIcon, Paperclip } from "lucide-react"
import { toast } from "sonner"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export function ActivityActionDialog({
  activity,
  mode,
  open,
  onOpenChange,
  onRefresh
}: {
  activity: any,
  mode: 'complete' | 'mitigate',
  open: boolean,
  onOpenChange: (open: boolean) => void,
  onRefresh: () => void
}) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    date: new Date(),
    reason: "",
    attachment: ""
  })

  const handleAction = async () => {
    setLoading(true)
    try {
      let endpoint = `${API_URL}/planning/activities/${activity.id}`
      let body: any = {}

      if (mode === 'complete') {
        body = { status: "Completed", completed_at: formData.date }
      } else {
        endpoint += "/mitigate"
        body = { reason: formData.reason, attachment_url: formData.attachment, new_due_date: formData.date }
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      })

      if (res.ok) {
        toast.success(mode === 'complete' ? "Task marked as completed" : "Task mitigated successfully")
        onRefresh()
        onOpenChange(false)
      } else {
        toast.error("An error occurred")
      }
    } catch (e) {
      toast.error("Connection failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="text-[#003D5C] flex items-center gap-2">
            {mode === 'complete' ? "Report Completion" : "Mitigate Activity"}
          </DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="space-y-1">
            <Label className="text-xs text-slate-500 uppercase font-bold tracking-wider">Activity</Label>
            <p className="text-sm font-medium text-[#003D5C]">{activity?.title}</p>
          </div>

          <div className="space-y-2">
            <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">
              {mode === 'complete' ? "Completion Date" : "New Due Date"}
            </Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-full justify-start text-left font-normal">
                  <CalIcon className="mr-2 h-4 w-4" />
                  {formData.date ? format(formData.date, "PPP") : <span>Pick a date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar mode="single" selected={formData.date} onSelect={(d) => d && setFormData({ ...formData, date: d })} initialFocus />
              </PopoverContent>
            </Popover>
          </div>

          {mode === 'mitigate' && (
            <>
              <div className="space-y-2">
                <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">Mitigation Reason</Label>
                <Textarea
                  placeholder="Explain why the task is being mitigated..."
                  className="resize-none"
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">Attachment (MocK URL)</Label>
                <div className="relative">
                  <Input
                    placeholder="https://example.com/proof.pdf"
                    className="pl-9"
                    value={formData.attachment}
                    onChange={(e) => setFormData({ ...formData, attachment: e.target.value })}
                  />
                  <Paperclip className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                </div>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            onClick={handleAction}
            disabled={loading}
            className={mode === 'complete' ? "bg-green-600 hover:bg-green-700 text-white" : "bg-slate-800 hover:bg-slate-900 text-white"}>
            {loading ? "Processing..." : mode === 'complete' ? "Complete Task" : "Save Mitigation"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function NewStrategyDialog({
  open,
  onOpenChange,
  onRefresh,
  fpsos,
  activityTypes
}: {
  open: boolean,
  onOpenChange: (open: boolean) => void,
  onRefresh: () => void,
  fpsos: string[],
  activityTypes: string[]
}) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    type: "",
    fpso: "",
    date: new Date(),
    responsible: "Current User"
  })

  const handleSubmit = async () => {
    if (!formData.title || !formData.type || !formData.fpso || !formData.date) {
      toast.error("Please fill in all required fields")
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/planning/activities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: formData.title,
          description: formData.description,
          type: formData.type,
          fpso_name: formData.fpso,
          scheduled_date: formData.date.toISOString(),
          responsible: formData.responsible,
          status: "Planned",
          duration_hours: 1
        })
      })

      if (res.ok) {
        toast.success("Strategy created successfully")
        onRefresh()
        onOpenChange(false)
        setFormData({
          title: "",
          description: "",
          type: "",
          fpso: "",
          date: new Date(),
          responsible: "Current User"
        })
      } else {
        toast.error("Failed to create strategy")
      }
    } catch (e) {
      toast.error("Connection failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-[#003D5C] font-bold">New Strategy</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">FPSO *</Label>
              <Select value={formData.fpso} onValueChange={(v) => setFormData({ ...formData, fpso: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select FPSO" />
                </SelectTrigger>
                <SelectContent>
                  {fpsos.map(f => <SelectItem key={f} value={f}>{f}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">Activity Type *</Label>
              <Select value={formData.type} onValueChange={(v) => setFormData({ ...formData, type: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Type" />
                </SelectTrigger>
                <SelectContent>
                  {activityTypes.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">Title *</Label>
            <Input
              placeholder="e.g. Monthly Calibration of Oil Export"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">Description</Label>
            <Textarea
              placeholder="Additional details..."
              className="resize-none"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">Scheduled Date *</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start text-left font-normal">
                    <CalIcon className="mr-2 h-4 w-4" />
                    {formData.date ? format(formData.date, "PPP") : <span>Pick a date</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar mode="single" selected={formData.date} onSelect={(d) => d && setFormData({ ...formData, date: d })} initialFocus />
                </PopoverContent>
              </Popover>
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-bold uppercase tracking-wider text-slate-500">Responsible</Label>
              <Input
                value={formData.responsible}
                onChange={(e) => setFormData({ ...formData, responsible: e.target.value })}
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="bg-[#FF6B35] hover:bg-[#e05a2b] text-white font-bold">
            {loading ? "Creating..." : "Create Strategy"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
