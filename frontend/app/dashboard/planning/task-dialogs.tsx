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
