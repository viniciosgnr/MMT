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
  FileText,
  Save,
  CheckCircle2,
  Activity
} from "lucide-react"
import { toast } from "sonner"
import { apiFetch } from "@/lib/api"

// Standard Analysis Types based on CDI + Generic
const ANALYSIS_TYPES = [
  "Specific Mass",
  "Viscosity",
  "PVT",
  "Chromatography",
  "Density",
  "BSW",
  "Enxofre"
]

const stripFpsoSuffix = (tag: string) => {
  if (!tag) return tag
  return tag.replace(/-(CDI|CDS|CDM|CDP|ESS|CPX|CDA|ADG|ATD|SEP)$/, "")
}

export default function NewSamplePage() {
  const router = useRouter()
  const [meters, setMeters] = useState<any[]>([])
  const [selectedFpso, setSelectedFpso] = useState<string>("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [formData, setFormData] = useState({
    sample_id: `SAM-${new Date().getFullYear()}-${Math.floor(Math.random() * 900) + 100}`,
    meter_id: "",
    sample_point_id: "",
    type: "",
    well_id: "",
    validation_party: "Client",
    is_active: "1",
    planned_date: new Date().toISOString().split('T')[0],
    responsible: "Lab Technician", // default or can be input
  })

  // Wells for test separator association
  const [wells, setWells] = useState<any[]>([])

  useEffect(() => {
    loadMeters()
  }, [])

  // Load wells when FPSO is selected
  useEffect(() => {
    if (selectedFpso) {
      loadWells(selectedFpso)
    } else {
      setWells([])
    }
  }, [selectedFpso])

  const loadWells = async (fpso: string) => {
    try {
      const res = await apiFetch(`/config/wells?fpso=${encodeURIComponent(fpso)}`)
      if (res.ok) {
        const data = await res.json()
        setWells(data.filter((w: any) => w.status === "Active"))
      }
    } catch (err) {
      console.error("Failed to load wells", err)
    }
  }

  const loadMeters = async () => {
    try {
      setIsLoading(true)
      const res = await apiFetch("/chemical/meters")
      if (res.ok) {
        setMeters(await res.json())
      } else {
        toast.error("Failed to load metering points")
      }
    } catch (error) {
      toast.error("Failed to load metering points")
    } finally {
      setIsLoading(false)
    }
  }

  const availableFpsos = Array.from(new Set(
    meters.flatMap(m => m.sample_points?.map((sp: any) => sp.fpso_name) || []).filter(Boolean)
  )).sort()

  const filteredMeters = selectedFpso
    ? meters.filter(m => m.sample_points?.some((sp: any) => sp.fpso_name === selectedFpso))
    : meters

  const selectedMeter = filteredMeters.find(m => m.id.toString() === formData.meter_id)
  const availableSamplePoints = selectedMeter?.sample_points?.filter((sp: any) => sp.fpso_name === selectedFpso) || []

  // Auto-fill classification if available
  const classification = selectedMeter?.classification || "—"

  // Determine if a Well selector should be shown
  // Test Separator Sample Points: T62-AP-2224 (Oil/PVT), T71-AP-0602 (Gas/Chromatography)
  const selectedSamplePoint = availableSamplePoints.find((sp: any) => sp.id.toString() === formData.sample_point_id)
  const selectedSpTag = selectedSamplePoint?.tag_number || ""
  const isTestSeparatorWithWell = (
    (selectedSpTag.includes("T62-AP-2224") && formData.type === "PVT") ||
    (selectedSpTag.includes("T71-AP-0602") && formData.type === "Chromatography")
  )
  const showWellSelector = isTestSeparatorWithWell && wells.length > 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (!formData.meter_id || !formData.sample_point_id || !formData.type) {
        toast.error("Please fill in all required fields (Meter, Sample Point, Analysis Type)")
        return
      }
      setIsSubmitting(true)

      const payload: any = {
        ...formData,
        meter_id: parseInt(formData.meter_id),
        sample_point_id: parseInt(formData.sample_point_id),
        is_active: parseInt(formData.is_active),
        well_id: formData.well_id ? parseInt(formData.well_id) : null,
      }

      const res = await apiFetch("/chemical/samples", {
        method: "POST",
        body: JSON.stringify(payload)
      })

      if (res.ok) {
        toast.success("Analysis Planned Successfully")
        router.push("/dashboard/chemical")
      } else {
        throw new Error("Failed API response")
      }
    } catch (error) {
      toast.error("Failed to plan analysis")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-4 border-b pb-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#003D5C]">Plan Analysis</h1>
          <p className="text-sm text-muted-foreground">Schedule a new periodic chemical analysis.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="shadow-sm border-slate-200">
          <CardHeader className="bg-slate-50/50 border-b pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Beaker className="w-5 h-5 text-primary" />
              Analysis Parameters
            </CardTitle>
            <CardDescription>Select the asset hierarchy and analysis requirements.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">

            {/* Row 1: FPSO and Sample ID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="fpso">FPSO Facility *</Label>
                <Select
                  value={selectedFpso}
                  onValueChange={v => {
                    setSelectedFpso(v)
                    // Reset meter and sample point when FPSO changes
                    setFormData({ ...formData, meter_id: "", sample_point_id: "" })
                  }}
                >
                  <SelectTrigger id="fpso" className="w-full">
                    <SelectValue placeholder={isLoading ? "Loading FPSOs..." : "Select FPSO"} />
                  </SelectTrigger>
                  <SelectContent>
                    {availableFpsos.map((fpso: any) => (
                      <SelectItem key={fpso} value={fpso}>{fpso}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="sample_id">Analysis/Sample ID</Label>
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
            </div>

            {/* Row 2: Metering Point and Sample Point */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="meter">Metering Point *</Label>
                <Select
                  value={formData.meter_id}
                  onValueChange={v => setFormData({ ...formData, meter_id: v, sample_point_id: "" })}
                  disabled={!selectedFpso}
                >
                  <SelectTrigger id="meter" className="w-full">
                    <SelectValue placeholder={!selectedFpso ? "Select FPSO first" : isLoading ? "Loading..." : "Select Metering Point"} />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px] overflow-y-auto">
                    {filteredMeters.map(m => (
                      <SelectItem key={m.id} value={m.id.toString()}>
                        {stripFpsoSuffix(m.tag_number)} {m.description ? `— ${m.description}` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {formData.meter_id && (
                  <p className="text-xs text-slate-500 mt-1">Classification: <span className="font-semibold text-slate-700">{classification}</span></p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="sample_point">Sample Point *</Label>
                <Select
                  value={formData.sample_point_id}
                  onValueChange={v => setFormData({ ...formData, sample_point_id: v })}
                  disabled={!formData.meter_id || availableSamplePoints.length === 0}
                >
                  <SelectTrigger id="sample_point" className="w-full">
                    <SelectValue placeholder={
                      !formData.meter_id ? "Select a Metering Point first..." :
                        availableSamplePoints.length === 0 ? "No Sample Points linked" :
                          "Select Sample Point"
                    } />
                  </SelectTrigger>
                  <SelectContent>
                    {availableSamplePoints.map((sp: any) => (
                      <SelectItem key={sp.id} value={sp.id.toString()}>
                        {stripFpsoSuffix(sp.tag_number)} {sp.description ? `— ${sp.description}` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Row 3: Type of Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="type">Type of Analysis *</Label>
                <Select value={formData.type} onValueChange={v => setFormData({ ...formData, type: v, well_id: "" })}>
                  <SelectTrigger id="type" className="w-full">
                    <SelectValue placeholder="Select Analysis" />
                  </SelectTrigger>
                  <SelectContent>
                    {ANALYSIS_TYPES.map(type => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="hidden md:block"></div>
            </div>

            {/* Conditional Row: Well Selection for Test Separator + PVT/Chromatography */}
            {showWellSelector && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-amber-50/60 border border-amber-200 rounded-lg p-4 -mx-1">
                <div className="space-y-2">
                  <Label htmlFor="well" className="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-amber-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2v20M8 6l4-4 4 4M6 10h12M7 14h10M8 18h8" />
                    </svg>
                    Well (Poço) *
                  </Label>
                  <Select value={formData.well_id} onValueChange={v => setFormData({ ...formData, well_id: v })}>
                    <SelectTrigger id="well" className="w-full bg-white">
                      <SelectValue placeholder="Select which Well this analysis is for..." />
                    </SelectTrigger>
                    <SelectContent>
                      {wells.map((w: any) => (
                        <SelectItem key={w.id} value={w.id.toString()}>
                          {w.tag} {w.description ? `— ${w.description}` : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-amber-700">
                    This Sample Point is a Test Separator associated with wells. Select the well being analyzed.
                  </p>
                </div>
                <div className="hidden md:block"></div>
              </div>
            )}

            {/* Row 3: Validation and Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-t pt-6 mt-2">
              <div className="space-y-2">
                <Label htmlFor="validation" className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Validation By
                </Label>
                <Select value={formData.validation_party} onValueChange={v => setFormData({ ...formData, validation_party: v })}>
                  <SelectTrigger id="validation" className="w-full">
                    <SelectValue placeholder="Select Validation Party" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Client">Client</SelectItem>
                    <SelectItem value="SBM offshore">SBM offshore</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="status" className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-600" />
                  Periodic Status
                </Label>
                <Select value={formData.is_active} onValueChange={v => setFormData({ ...formData, is_active: v })}>
                  <SelectTrigger id="status" className="w-full">
                    <SelectValue placeholder="Select Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">Active</SelectItem>
                    <SelectItem value="0">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

          </CardContent>
        </Card>

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="outline" type="button" onClick={() => router.back()}>Cancel</Button>
          <Button type="submit" disabled={isSubmitting || !formData.meter_id || !formData.sample_point_id || !formData.type || (showWellSelector && !formData.well_id)}>
            {isSubmitting ? "Planning Analysis..." : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Plan Analysis
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
