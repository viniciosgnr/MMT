"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"

interface SyncSourceDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: () => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export function SyncSourceDialog({ open, onOpenChange, onCreated }: SyncSourceDialogProps) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    type: "FLOW_COMPUTER",
    fpso: "",
    connection_details: ""
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/sync/sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      })

      if (res.ok) {
        toast.success("Sync source registered successfully")
        onCreated()
        onOpenChange(false)
        setFormData({ name: "", type: "FLOW_COMPUTER", fpso: "", connection_details: "" })
      } else {
        toast.error("Failed to register sync source")
      }
    } catch (error) {
      toast.error("An error occurred")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Register Sync Source</DialogTitle>
            <DialogDescription>
              Configure a new connection for data ingestion from offshore systems.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Source Name</Label>
              <Input
                id="name"
                placeholder="e.g. FPSO SEPETIBA - Omni 6000"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="type">Source Type</Label>
              <Select
                value={formData.type}
                onValueChange={(value) => setFormData({ ...formData, type: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="FLOW_COMPUTER">Flow Computer (Omni/Floboss/ABB)</SelectItem>
                  <SelectItem value="AVEVA_PI">AVEVA PI Server</SelectItem>
                  <SelectItem value="MANUAL_FILE">Manual File Dump (Contractor Software)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="fpso">FPSO Unit</Label>
              <Input
                id="fpso"
                placeholder="e.g. FPSO PARATY"
                value={formData.fpso}
                onChange={(e) => setFormData({ ...formData, fpso: e.target.value })}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="details">Connection Configuration (Optional JSON)</Label>
              <Input
                id="details"
                placeholder='{"ip": "10.0.0.1", "port": 502}'
                value={formData.connection_details}
                onChange={(e) => setFormData({ ...formData, connection_details: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700">
              {loading ? "Registering..." : "Register Source"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
