"use client"

import { useState, useEffect } from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Search, Plus, FileText, Settings, ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import { fetchEquipments as fetchEquipmentsAPI, createEquipment } from "@/lib/api"

export default function EquipmentInventory() {
  const [equipments, setEquipments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [form, setForm] = useState({
    serial_number: "",
    model: "",
    manufacturer: "",
    equipment_type: "Pressure Transmitter",
    calibration_frequency_months: 12,
    calculation_base: "Calibration Date",
    status: "Active"
  })

  useEffect(() => {
    fetchEquipments()
  }, [])

  async function fetchEquipments() {
    try {
      setLoading(true)
      const data = await fetchEquipmentsAPI()
      if (Array.isArray(data)) {
        setEquipments(data)
      } else {
        setEquipments([])
      }
    } catch (error) {
      console.error("Error fetching equipments:", error)
      toast.error("Failed to load equipment inventory")
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister() {
    if (!form.serial_number || !form.model) {
      toast.error("Please fill in the required fields.")
      return
    }

    try {
      setSubmitting(true)
      await createEquipment(form)
      toast.success("Equipment registered successfully!")
      setIsDialogOpen(false)
      fetchEquipments()
      setForm({
        serial_number: "",
        model: "",
        manufacturer: "",
        equipment_type: "Pressure Transmitter",
        calibration_frequency_months: 12,
        calculation_base: "Calibration Date",
        status: "Active"
      })
    } catch (error: any) {
      toast.error(error.message || "Failed to register equipment")
    } finally {
      setSubmitting(false)
    }
  }

  const filtered = equipments.filter(eq =>
    eq.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    eq.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
    eq.manufacturer?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-4">
      <Card className="border-none shadow-none bg-transparent">
        <CardContent className="p-0 flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by Serial Number, Model or Manufacturer..."
              className="pl-9 bg-white"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#FF6B35] hover:bg-[#e05a2b] text-white shadow-lg shadow-orange-500/10">
                <Plus className="mr-2 h-4 w-4" /> Register New Device
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle className="text-[#003D5C]">Register Physical Equipment</DialogTitle>
                <DialogDescription>
                  Enter the hardware details as per the manufacturer's nameplate.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-6 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="serial_number">Serial Number *</Label>
                    <Input
                      id="serial_number"
                      placeholder="e.g. SN123456"
                      value={form.serial_number}
                      onChange={(e) => setForm({ ...form, serial_number: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="model">Model *</Label>
                    <Input
                      id="model"
                      placeholder="e.g. 3051S"
                      value={form.model}
                      onChange={(e) => setForm({ ...form, model: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="manufacturer">Manufacturer</Label>
                    <Input
                      id="manufacturer"
                      placeholder="e.g. Emerson"
                      value={form.manufacturer}
                      onChange={(e) => setForm({ ...form, manufacturer: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="type">Equipment Type</Label>
                    <Select value={form.equipment_type} onValueChange={(v) => setForm({ ...form, equipment_type: v })}>
                      <SelectTrigger id="type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Pressure Transmitter">Pressure Transmitter</SelectItem>
                        <SelectItem value="Temperature Transmitter">Temperature Transmitter</SelectItem>
                        <SelectItem value="Flow Meter (USM)">Flow Meter (USM)</SelectItem>
                        <SelectItem value="Flow Meter (Coriolis)">Flow Meter (Coriolis)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cal_freq">Calibration Frequency (Months)</Label>
                    <Input
                      id="cal_freq"
                      type="number"
                      value={form.calibration_frequency_months}
                      onChange={(e) => setForm({ ...form, calibration_frequency_months: parseInt(e.target.value) })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cal_base">Calculation Base</Label>
                    <Select value={form.calculation_base} onValueChange={(v) => setForm({ ...form, calculation_base: v })}>
                      <SelectTrigger id="cal_base">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Calibration Date">Calibration Date</SelectItem>
                        <SelectItem value="Installation Date">Installation Date</SelectItem>
                        <SelectItem value="Both">Both</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button
                  className="bg-[#FF6B35] hover:bg-[#e05a2b] text-white"
                  onClick={handleRegister}
                  disabled={submitting}
                >
                  {submitting ? "Registering..." : "Complete Registration"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-50">
            <TableRow>
              <TableHead className="font-bold text-[#003D5C]">Serial Number</TableHead>
              <TableHead className="font-bold text-[#003D5C]">Manufacturer</TableHead>
              <TableHead className="font-bold text-[#003D5C]">Model</TableHead>
              <TableHead className="font-bold text-[#003D5C]">Type</TableHead>
              <TableHead className="font-bold text-[#003D5C]">Status</TableHead>
              <TableHead className="font-bold text-[#003D5C]">Certificates</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-10">Loading inventory...</TableCell>
              </TableRow>
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-10 text-muted-foreground">
                  No physical equipment found matching your search.
                </TableCell>
              </TableRow>
            ) : filtered.map((eq) => (
              <TableRow key={eq.id} className="hover:bg-slate-50/50">
                <TableCell className="font-mono font-bold text-[#003D5C]">{eq.serial_number}</TableCell>
                <TableCell>{eq.manufacturer || "N/A"}</TableCell>
                <TableCell>{eq.model}</TableCell>
                <TableCell>{eq.equipment_type}</TableCell>
                <TableCell>
                  <Badge
                    variant={eq.status === 'Active' ? 'default' : 'secondary'}
                    className={eq.status === 'Active' ? 'bg-emerald-500 hover:bg-emerald-600' : ''}
                  >
                    {eq.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex -space-x-1">
                    <div title="Calibration Certificate" className="h-6 w-6 rounded-full bg-blue-100 border border-white flex items-center justify-center">
                      <ShieldCheck className="h-3 w-3 text-blue-600" />
                    </div>
                    <div title="Technical Datasheet" className="h-6 w-6 rounded-full bg-orange-100 border border-white flex items-center justify-center">
                      <FileText className="h-3 w-3 text-orange-600" />
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="icon" title="Settings">
                    <Settings className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
