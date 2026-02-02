"use client"

import { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { apiFetch } from "@/lib/api"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

interface NewCardDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: () => void
  initialColumnId?: number | null
}

export function NewCardDialog({ open, onOpenChange, onCreated, initialColumnId = null }: NewCardDialogProps) {
  const [columns, setColumns] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    fpso: "",
    column_id: "",
    responsible: "Daniel Bernoulli"
  })

  useEffect(() => {
    if (open) {
      apiFetch("/maintenance/columns")
        .then(res => res.json())
        .then(data => {
          setColumns(data)
          if (initialColumnId) {
            setFormData(prev => ({ ...prev, column_id: initialColumnId.toString() }))
          } else if (data.length > 0 && !formData.column_id) {
            setFormData(prev => ({ ...prev, column_id: data[0].id.toString() }))
          }
        }).catch(err => console.error("Failed to load columns", err))
    }
  }, [open, initialColumnId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title || !formData.fpso || !formData.column_id) {
      toast.error("Please fill in all required fields")
      return
    }

    try {
      setLoading(true)
      const res = await apiFetch("/maintenance/cards", {
        method: "POST",
        body: JSON.stringify({
          ...formData,
          column_id: parseInt(formData.column_id)
        })
      })

      if (res.ok) {
        toast.success("Maintenance card created successfully")
        onCreated()
        onOpenChange(false)
        setFormData({
          title: "",
          description: "",
          fpso: "",
          column_id: columns[0]?.id?.toString() || "",
          responsible: "Daniel Bernoulli"
        })
      } else {
        toast.error("Failed to create card")
      }
    } catch (error) {
      toast.error("Connection error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Maintenance Card</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="title">Task Title *</Label>
            <Input
              id="title"
              placeholder="e.g. Recalibrate Fiscal Flow Meter"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="fpso">FPSO *</Label>
              <Select
                value={formData.fpso}
                onValueChange={(v) => setFormData({ ...formData, fpso: v })}
              >
                <SelectTrigger id="fpso">
                  <SelectValue placeholder="Select FPSO" />
                </SelectTrigger>
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
              <Label htmlFor="column">Initial Status *</Label>
              <Select
                value={formData.column_id}
                onValueChange={(v) => setFormData({ ...formData, column_id: v })}
              >
                <SelectTrigger id="column">
                  <SelectValue placeholder="Select column" />
                </SelectTrigger>
                <SelectContent>
                  {columns.map((col) => (
                    <SelectItem key={col.id} value={col.id.toString()}>
                      {col.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Provide context for this maintenance task..."
              className="min-h-[100px]"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white">
              {loading ? "Creating..." : "Create Card"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
