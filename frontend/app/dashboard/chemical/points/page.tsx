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
  AlertCircle,
  Filter,
  Search,
} from "lucide-react"
import { apiFetch } from "@/lib/api"
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

const FPSO_LIST = [
  "CDS - Cidade de Saquarema",
  "CDM - Cidade de Maricá",
  "CDI - Cidade de Ilhabela",
  "CDP - Cidade de Paraty",
  "ESS - Espírito Santo",
  "CPX - Capixaba",
  "CDA - Cidade de Anchieta",
  "ADG - Alexandre de Gusmão",
  "ATD - Almirante Tamandaré",
  "SEP - Sepetiba",
]

export default function SamplePointConfigPage() {
  const router = useRouter()
  const [points, setPoints] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [fpsoFilter, setFpsoFilter] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")

  const [newPoint, setNewPoint] = useState({
    tag_number: "",
    description: "",
    fpso_name: FPSO_LIST[0],
    sampling_interval_days: 30,
    is_operational: 1,
    validation_method_implemented: 0
  })

  useEffect(() => {
    loadPoints()
  }, [])

  const loadPoints = async () => {
    try {
      setIsLoading(true)
      const res = await apiFetch("/chemical/sample-points")
      if (res.ok) {
        setPoints(await res.json())
      } else {
        toast.error("Failed to load sample points")
      }
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

      const res = await apiFetch("/chemical/sample-points", {
        method: "POST",
        body: JSON.stringify(newPoint)
      })

      if (res.ok) {
        toast.success("Sample point created successfully")
        setIsDialogOpen(false)
        loadPoints()
      } else {
        toast.error("Failed to create sample point")
      }
    } catch (error) {
      toast.error("Failed to create sample point")
    }
  }

  // Apply filters
  const filteredPoints = points.filter(p => {
    if (fpsoFilter !== "all" && p.fpso_name !== fpsoFilter) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return (
        p.tag_number?.toLowerCase().includes(q) ||
        p.description?.toLowerCase().includes(q) ||
        p.fpso_name?.toLowerCase().includes(q)
      )
    }
    return true
  })

  // Count per FPSO for the badges
  const fpsoCounts: Record<string, number> = {}
  points.forEach(p => {
    fpsoCounts[p.fpso_name] = (fpsoCounts[p.fpso_name] || 0) + 1
  })

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
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
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-sm px-3 py-1">
            {points.length} points total
          </Badge>
          <Button onClick={() => setIsDialogOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Point
          </Button>
        </div>
      </div>

      {/* FPSO Filter Tabs */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={fpsoFilter === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setFpsoFilter("all")}
          className="text-xs"
        >
          All FPSOs
          <Badge variant="secondary" className="ml-1.5 text-[10px] h-5 px-1.5">{points.length}</Badge>
        </Button>
        {FPSO_LIST.map(fpso => {
          const count = fpsoCounts[fpso] || 0
          if (count === 0) return null
          const abbr = fpso.split(" - ")[0]
          return (
            <Button
              key={fpso}
              variant={fpsoFilter === fpso ? "default" : "outline"}
              size="sm"
              onClick={() => setFpsoFilter(fpso)}
              className="text-xs"
            >
              {abbr}
              <Badge variant="secondary" className="ml-1.5 text-[10px] h-5 px-1.5">{count}</Badge>
            </Button>
          )
        })}
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search by tag, description..."
          className="pl-9"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between">
              <span>
                {fpsoFilter === "all" ? "All Sample Points" : fpsoFilter}
              </span>
              <Badge variant="outline">{filteredPoints.length} results</Badge>
            </CardTitle>
            <CardDescription>
              {fpsoFilter === "all"
                ? "Fiscal measurement points across the fleet."
                : `Sample points for ${fpsoFilter}.`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tag Number</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>FPSO</TableHead>
                  <TableHead>Interval</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-10">Loading...</TableCell>
                  </TableRow>
                ) : filteredPoints.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-10 text-muted-foreground">
                      {searchQuery ? "No points match your search." : "No sample points configured."}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredPoints.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-bold text-primary">{p.tag_number}</TableCell>
                      <TableCell>{p.description}</TableCell>
                      <TableCell>
                        <span className="text-xs">{p.fpso_name}</span>
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
        <DialogContent className="sm:max-w-[500px] max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Sample Point</DialogTitle>
            <DialogDescription>Define a new physical sampling point for the fiscal metering system.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tag Number *</Label>
                <Input placeholder="e.g., T77-FT-0103" value={newPoint.tag_number} onChange={e => setNewPoint({ ...newPoint, tag_number: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>FPSO</Label>
                <Select value={newPoint.fpso_name} onValueChange={v => setNewPoint({ ...newPoint, fpso_name: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {FPSO_LIST.map(fpso => (
                      <SelectItem key={fpso} value={fpso}>{fpso}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Description *</Label>
              <Input placeholder="e.g., Fuel Gas, HP Flare, Export Gas" value={newPoint.description} onChange={e => setNewPoint({ ...newPoint, description: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Sampling Interval (Days)</Label>
              <Input type="number" value={newPoint.sampling_interval_days} onChange={e => setNewPoint({ ...newPoint, sampling_interval_days: parseInt(e.target.value) })} />
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
