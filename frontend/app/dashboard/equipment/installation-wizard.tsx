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

      const tagRes = await apiFetch("/equipment/tags")
      if (tagRes.ok) {
        setTags(await tagRes.json())
      }
    } catch (e) {
      console.error(e)
      toast.error("Failed to load resources")
    }
  }

  const handleNext = () => {
    if (step === 1 && (!selectedEq || !selectedTag)) {
      toast.error("Select Equipment and Tag")
      return
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
      const res = await apiFetch("/equipment/install", {
        method: "POST",
        body: JSON.stringify({
          equipment_id: parseInt(selectedEq),
          tag_id: parseInt(selectedTag),
          installed_by: installedBy,
          // Send checklist data as serialized JSON string
          // In a real app, this would be validated by Schema
          // We added `checklist_data` to schemas.py
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
                  <SelectContent>
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
                    <SelectValue placeholder="Select Tag..." />
                  </SelectTrigger>
                  <SelectContent>
                    {tags.map(tag => (
                      <SelectItem key={tag.id} value={tag.id.toString()}>
                        {tag.tag_number} - {tag.description}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
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
                  <span className="text-xs font-bold text-slate-500 uppercase">Tag:</span>
                  <span className="text-xs font-black text-[#FF6B35]">
                    {tags.find(t => t.id.toString() === selectedTag)?.tag_number}
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
