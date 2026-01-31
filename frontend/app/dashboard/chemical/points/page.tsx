"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import {
  ArrowLeft,
  Plus,
  Settings,
  Link as LinkIcon,
  Activity,
  Save,
  Trash2,
  AlertCircle
} from "lucide-react"
import {
  fetchSamplePoints,
  createSamplePoint,
  fetchEquipments // Using this to mock fetching available tags if needed, but better use a specific one
} from "@/lib/api"
import { toast } from "sonner"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"

export default function SamplePointConfigPage() {
  const router = useRouter()
  const [points, setPoints] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const [newPoint, setNewPoint] = useState({
    tag_number: "",
    description: "",
    fpso_name: "FPSO PARATY",
    fluid_type: "Gas",
    sampling_interval_days: 30,
    is_operational: 1,
    validation_method_implemented: 1
  })

  useEffect(() => {
    loadPoints()
  }, [])

  const loadPoints = async () => {
    try {
      setIsLoading(true)
      const data = await fetchSamplePoints()
      setPoints(data)
    } catch (error) {
      toast.error("Failed to load sample points")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreatePoint = async () => {
    try {
      if (!newPoint.tag_number || !newPoint.description) {
        toast.error("Please fill in all required fields")
        return
      }
      await createSamplePoint(newPoint)
      toast.success("Sample point created successfully")
      setIsDialogOpen(false)
      loadPoints()
    } catch (error) {
      toast.error("Failed to create sample point")
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Sample Point Configuration</h1>
            <p className="text-sm text-muted-foreground">Manage physical sampling points and their metrological associations.</p>
          </div>
        </div>
        <Button onClick={() => setIsDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Point
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Active Sample Points</CardTitle>
            <CardDescription>Fiscal measurement points across the fleet.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tag Number</TableHead>
                  <TableHead>Location / Description</TableHead>
                  <TableHead>FPSO</TableHead>
                  <TableHead>Fluid Type</TableHead>
                  <TableHead>Interval</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-10">Loading...</TableCell>
                  </TableRow>
                ) : points.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-10 text-muted-foreground">No sample points configured.</TableCell>
                  </TableRow>
                ) : (
                  points.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-bold">{p.tag_number}</TableCell>
                      <TableCell>{p.description}</TableCell>
                      <TableCell>{p.fpso_name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{p.fluid_type}</Badge>
                      </TableCell>
                      <TableCell>{p.sampling_interval_days} days</TableCell>
                      <TableCell>
                        <Badge className={p.is_operational ? "bg-green-600" : "bg-slate-400"}>
                          {p.is_operational ? "Operational" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="sm" title="Link Tags">
                            <LinkIcon className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-red-500">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* New Point Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add New Sample Point</DialogTitle>
            <DialogDescription>Define a new physical sampling point for the fiscal metering system.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tag Number *</Label>
                <Input placeholder="e.g., 62-SP-1101" value={newPoint.tag_number} onChange={e => setNewPoint({ ...newPoint, tag_number: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>FPSO</Label>
                <Select value={newPoint.fpso_name} onValueChange={v => setNewPoint({ ...newPoint, fpso_name: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FPSO PARATY">FPSO PARATY</SelectItem>
                    <SelectItem value="FPSO SEPETIBA">FPSO SEPETIBA</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Description *</Label>
              <Input placeholder="Description of sampling location" value={newPoint.description} onChange={e => setNewPoint({ ...newPoint, description: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Fluid Type</Label>
                <Select value={newPoint.fluid_type} onValueChange={v => setNewPoint({ ...newPoint, fluid_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Gas">Gas</SelectItem>
                    <SelectItem value="Oil">Oil</SelectItem>
                    <SelectItem value="Water">Water</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Sampling Interval (Days)</Label>
                <Input type="number" value={newPoint.sampling_interval_days} onChange={e => setNewPoint({ ...newPoint, sampling_interval_days: parseInt(e.target.value) })} />
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
              <div className="space-y-0.5">
                <Label>SBM Validation</Label>
                <p className="text-xs text-muted-foreground">Enable statistical analysis for this point.</p>
              </div>
              <Switch checked={newPoint.validation_method_implemented === 1} onCheckedChange={checked => setNewPoint({ ...newPoint, validation_method_implemented: checked ? 1 : 0 })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleCreatePoint}>Create Sample Point</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
