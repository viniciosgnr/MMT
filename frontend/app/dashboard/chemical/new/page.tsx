"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ArrowLeft,
  Beaker,
  Calendar,
  User,
  FileText,
  Save,
  Plus
} from "lucide-react"
import {
  fetchSamplePoints,
  createSample
} from "@/lib/api"
import { toast } from "sonner"
import { Textarea } from "@/components/ui/textarea"

export default function NewSamplePage() {
  const router = useRouter()
  const [samplePoints, setSamplePoints] = useState<any[]>([])
  const [isLoadingPoints, setIsLoadingPoints] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [formData, setFormData] = useState({
    sample_id: `SAM-${new Date().getFullYear()}-${Math.floor(Math.random() * 900) + 100}`,
    sample_point_id: "",
    planned_date: new Date().toISOString().split('T')[0],
    responsible: "",
    notes: ""
  })

  useEffect(() => {
    loadPoints()
  }, [])

  const loadPoints = async () => {
    try {
      setIsLoadingPoints(true)
      const data = await fetchSamplePoints()
      setSamplePoints(data)
    } catch (error) {
      toast.error("Failed to load sample points")
    } finally {
      setIsLoadingPoints(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (!formData.sample_point_id || !formData.sample_id || !formData.responsible) {
        toast.error("Please fill in all required fields")
        return
      }
      setIsSubmitting(true)

      const selectedPoint = samplePoints.find(p => p.id === parseInt(formData.sample_point_id))

      await createSample({
        ...formData,
        sample_point_id: parseInt(formData.sample_point_id),
        type: selectedPoint?.fluid_type || "Gas"
      })

      toast.success("Sample planned successfully")
      router.push("/dashboard/chemical")
    } catch (error) {
      toast.error("Failed to plan sample")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Plan New Sample</h1>
          <p className="text-sm text-muted-foreground">Initialize a new fiscal sampling process in the system.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sample Identification</CardTitle>
            <CardDescription>Enter the basic identification and planning details.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sample_id">Sample ID (Barcode/Unique)</Label>
                <div className="relative">
                  <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="sample_id"
                    placeholder="e.g. SAM-2024-002"
                    className="pl-10"
                    value={formData.sample_id}
                    onChange={e => setFormData({ ...formData, sample_id: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="sample_point">Sample Point *</Label>
                <Select value={formData.sample_point_id} onValueChange={v => setFormData({ ...formData, sample_point_id: v })}>
                  <SelectTrigger id="sample_point" className="w-full">
                    <SelectValue placeholder={isLoadingPoints ? "Loading points..." : "Select point"} />
                  </SelectTrigger>
                  <SelectContent>
                    {samplePoints.map(p => (
                      <SelectItem key={p.id} value={p.id.toString()}>
                        {p.tag_number} - {p.description} ({p.fluid_type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="planned_date">Target Sampling Date</Label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="planned_date"
                    type="date"
                    className="pl-10"
                    value={formData.planned_date}
                    onChange={e => setFormData({ ...formData, planned_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="responsible">Responsible Person *</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="responsible"
                    placeholder="Engineer or Technician"
                    className="pl-10"
                    value={formData.responsible}
                    onChange={e => setFormData({ ...formData, responsible: e.target.value })}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Initial Notes / Context</Label>
              <Textarea
                id="notes"
                placeholder="Specific instructions for the sampling team, cylinder identification, etc."
                className="min-h-[100px]"
                value={formData.notes}
                onChange={e => setFormData({ ...formData, notes: e.target.value })}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button variant="outline" type="button" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Planning Mobile..." : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Initialize Process
              </>
            )}
          </Button>
        </div>
      </form>

      <Card className="bg-primary/5 border-primary/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Beaker className="w-4 h-4 text-primary" />
            Process Note
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Initializing this process will set the status to <Badge variant="secondary" className="text-[10px] h-4">Planned</Badge>.
            The team on board will receive a notification to perform the physical sampling on the specified date.
            Once sampled, the full 11-step audit trail will begin tracking SLA milestones.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
