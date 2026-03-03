"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
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
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ArrowRight, Check, Hammer, AlertTriangle } from "lucide-react"
import { toast } from "sonner"
import { apiFetch } from "@/lib/api"

// Requirements from Spec Appendix D (Simplified for MVP Visualization)
const CHECKLIST_ITEMS = [
  { id: "visual_check", label: "Visual inspection of equipment condition performed?" },
  { id: "tag_match", label: "Verified Tag Number matches P&ID?" },
  { id: "cleaning", label: "Flange faces cleaned and inspected?" },
  { id: "gasket", label: "New gaskets installed?" },
  { id: "calibration", label: "Valid Calibration Certificate verified?" },
  { id: "sealing", label: "Equipment sealed after installation?" }
]

export function InstallationWizard({ onSuccess }: { onSuccess: () => void }) {
  const [open, setOpen] = useState(false)
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)

  // Data
  const [equipments, setEquipments] = useState<any[]>([])
  const [tags, setTags] = useState<any[]>([])

  // Form State
  const [selectedEq, setSelectedEq] = useState("")
  const [selectedTag, setSelectedTag] = useState("")
  const [checklist, setChecklist] = useState<Record<string, boolean>>({})
  const [installedBy, setInstalledBy] = useState("Technician Base")
  const [manualTag, setManualTag] = useState("") // For Sample Point

  // Derived state
  const eq = equipments.find(e => e.id.toString() === selectedEq)
  const targetTagNode = tags.find(t => t.id.toString() === selectedTag)

  const generatedTag = (): string => {
    if (!eq || !targetTagNode) return ""
    // Tag generation logic
    const bTag = targetTagNode.tag_number // e.g. T73-FT-5201
    const tType = eq.equipment_type

    if (tType === "Sample Point") return manualTag

    // Auto-replace FT with proper code
    if (tType === "Pressure Transmitter") return bTag.replace("-FT-", "-PT-")
    if (tType === "Temperature Transmitter") return bTag.replace("-FT-", "-TT-")
    if (tType === "Temperature Element") return bTag.replace("-FT-", "-TE-")
    return bTag // Fallback
  }

  useEffect(() => {
    if (open) {
      loadData()
      setStep(1)
      setChecklist({})
    }
  }, [open])

  const loadData = async () => {
    try {
      // Fetch only available equipment (simplified logic: filters could be better in backend)
      const eqRes = await apiFetch("/equipment")
      if (eqRes.ok) {
        setEquipments(await eqRes.json())
      }

      const tagRes = await apiFetch("/equipment/tags?limit=1000")
      if (tagRes.ok) {
        const allTags = await tagRes.json()
        // Only allow installation onto Metering Points (-FT-)
        const meteringPoints = allTags.filter((t: any) => t.tag_number.includes("-FT-"))
        setTags(meteringPoints)
      }
    } catch (e) {
      console.error(e)
      toast.error("Failed to load resources")
    }
  }

  const handleNext = () => {
    if (step === 1) {
      if (!selectedEq || !selectedTag) {
        toast.error("Select Equipment and Target Location")
        return
      }
      if (eq?.equipment_type === "Sample Point" && !manualTag.trim()) {
        toast.error("Enter Sample Point Tag")
        return
      }
    }
    setStep(step + 1)
  }

  const handleInstall = async () => {
    // Validate checklist
    const completed = CHECKLIST_ITEMS.every(item => checklist[item.id])
    if (!completed) {
      toast.error("All checklist items must be completed")
      return
    }

    setLoading(true)
    try {
      const urlParams = new URLSearchParams()
      urlParams.append("target_tag_name", generatedTag())
      urlParams.append("target_description", `${eq?.equipment_type} installed at ${targetTagNode?.tag_number}`)

      // If we could link the node ID to the Target Tag Location node... for now we pass generic info

      const res = await apiFetch(`/equipment/install?${urlParams.toString()}`, {
        method: "POST",
        body: JSON.stringify({
          equipment_id: parseInt(selectedEq),
          tag_id: 0, // 0 triggers creation of new tag from target_tag_name
          installed_by: installedBy,
          checklist_data: JSON.stringify(checklist)
        })
      })

      if (res.ok) {
        toast.success("Equipment successfully installed")
        setOpen(false)
        onSuccess()
      } else {
        throw new Error("Installation failed")
      }
    } catch (error) {
      console.error(error)
      toast.error("Installation failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-[#FF6B35] hover:bg-[#E55A2B] text-white font-black text-xs uppercase tracking-widest rounded-full shadow-md">
          <Hammer className="mr-2 h-4 w-4" /> Install Equipment (Workflow)
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="text-[#003D5C] font-black flex items-center gap-2">
            <Hammer className="h-5 w-5" /> Installation Wizard - Step {step} of 3
          </DialogTitle>
          <DialogDescription className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            {step === 1 ? "Select Components" : step === 2 ? "Mandatory Checklist (Spec 6.3)" : "Confirmation"}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {step === 1 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Equipment (Serial Number)</Label>
                <Select value={selectedEq} onValueChange={setSelectedEq}>
                  <SelectTrigger className="font-bold text-[#003D5C]">
                    <SelectValue placeholder="Select Equipment..." />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]">
                    {equipments.map(eq => (
                      <SelectItem key={eq.id} value={eq.id.toString()}>
                        {eq.serial_number} - {eq.equipment_type} ({eq.model})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Target Tag (Location)</Label>
                <Select value={selectedTag} onValueChange={setSelectedTag}>
                  <SelectTrigger className="font-bold text-[#FF6B35]">
                    <SelectValue placeholder="Select Target Location..." />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]">
                    {tags.map(tag => (
                      <SelectItem key={tag.id} value={tag.id.toString()}>
                        {tag.tag_number} - {tag.description}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {eq && targetTagNode && (
                <div className="space-y-2 pt-2 border-t border-slate-100">
                  <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                    Generated Instrument Tag
                  </Label>
                  {eq.equipment_type === "Sample Point" ? (
                    <Input
                      placeholder="e.g. T73-AP-1111"
                      value={manualTag}
                      onChange={(e) => setManualTag(e.target.value)}
                      className="font-bold text-emerald-600 border-emerald-200 focus-visible:ring-emerald-500"
                    />
                  ) : (
                    <div className="bg-emerald-50 text-emerald-700 font-mono font-bold px-3 py-2 rounded-md border border-emerald-200">
                      {generatedTag()}
                    </div>
                  )}
                  <p className="text-[10px] text-muted-foreground">
                    This tag will be created and bound to the equipment.
                  </p>
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="bg-amber-50 border border-amber-200 p-3 rounded-md mb-4 flex gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" />
                <p className="text-xs text-amber-800 font-medium">
                  Ensure all physical checks are performed. This will be logged in the audit trail.
                </p>
              </div>
              <div className="space-y-3">
                {CHECKLIST_ITEMS.map((item) => (
                  <div key={item.id} className="flex items-center space-x-2 border-b border-slate-100 pb-2 last:border-0">
                    <Checkbox
                      id={item.id}
                      checked={checklist[item.id] || false}
                      onCheckedChange={(c) => setChecklist(prev => ({ ...prev, [item.id]: !!c }))}
                    />
                    <label
                      htmlFor={item.id}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer text-[#003D5C]"
                    >
                      {item.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-lg space-y-2 border border-slate-200">
                <div className="flex justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase">Equipment:</span>
                  <span className="text-xs font-black text-[#003D5C]">
                    {equipments.find(e => e.id.toString() === selectedEq)?.serial_number}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase">Target Tag:</span>
                  <span className="text-xs font-black text-[#FF6B35]">
                    {generatedTag()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase">Checklist:</span>
                  <span className="text-xs font-black text-emerald-600">
                    {Object.values(checklist).filter(Boolean).length}/{CHECKLIST_ITEMS.length} Verified
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Technician Signature (Name)</Label>
                <Input
                  value={installedBy}
                  onChange={(e) => setInstalledBy(e.target.value)}
                  className="font-bold text-[#003D5C]"
                />
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex justify-between sm:justify-between">
          {step > 1 ? (
            <Button variant="ghost" onClick={() => setStep(step - 1)}>Back</Button>
          ) : <div />}

          {step < 3 ? (
            <Button onClick={handleNext} className="bg-[#003D5C]">Next <ArrowRight className="ml-2 h-4 w-4" /></Button>
          ) : (
            <Button onClick={handleInstall} disabled={loading} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold">
              {loading ? "Installing..." : "Confirm Installation"} <Check className="ml-2 h-4 w-4" />
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
