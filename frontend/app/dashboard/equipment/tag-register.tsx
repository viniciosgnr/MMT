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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Search, MapPin, Replace, History, Info, Plus } from "lucide-react"
import { toast } from "sonner"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export default function TagRegister() {
  const [tags, setTags] = useState<any[]>([])
  const [availableEquipment, setAvailableEquipment] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [installDialogOpen, setInstallDialogOpen] = useState(false)
  const [selectedTag, setSelectedTag] = useState<any>(null)
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<string>("")
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchTags()
    fetchAvailableEquipment()
  }, [])

  async function fetchTags() {
    try {
      setLoading(true)
      const res = await fetch(`${API_URL}/equipment/tags`)
      if (res.ok) {
        const data = await res.json()
        setTags(data)
      }
    } catch (error) {
      console.error("Error fetching tags:", error)
    } finally {
      setLoading(false)
    }
  }

  async function fetchAvailableEquipment() {
    try {
      // For now, let's just fetch all and filter client side if needed, 
      // but ideally we have an endpoint for uninstalled equipment.
      const res = await fetch(`${API_URL}/equipment/`)
      if (res.ok) {
        const data = await res.json()
        // Filter those without active installations would be better on backend
        // For simplicity, we'll just show all active ones for now
        setAvailableEquipment(data.filter((eq: any) => eq.status === "Active"))
      }
    } catch (error) {
      console.error("Error fetching available equipment:", error)
    }
  }

  async function handleInstall() {
    if (!selectedEquipmentId || !selectedTag) return

    try {
      setSubmitting(true)
      const res = await fetch(`${API_URL}/equipment/install`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equipment_id: parseInt(selectedEquipmentId),
          tag_id: selectedTag.id,
          installed_by: "Daniel Bernoulli" // Hardcoded for demo
        })
      })

      if (res.ok) {
        toast.success(`Equipment successfully installed on ${selectedTag.tag_number}`)
        setInstallDialogOpen(false)
        fetchTags()
        fetchAvailableEquipment()
      } else {
        const err = await res.json()
        toast.error(err.detail || "Installation failed")
      }
    } catch (error) {
      toast.error("Connection error")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRemove(tagId: number, installationId: number) {
    if (!confirm("Are you sure you want to remove the equipment from this tag?")) return

    try {
      const res = await fetch(`${API_URL}/equipment/remove/${installationId}`, {
        method: "POST"
      })

      if (res.ok) {
        toast.success("Equipment removed from tag.")
        fetchTags()
        fetchAvailableEquipment()
      } else {
        toast.error("Removal failed.")
      }
    } catch (error) {
      toast.error("Connection error")
    }
  }

  const filtered = tags.filter(tag =>
    tag.tag_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tag.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-4">
      <Card className="border-none shadow-none bg-transparent">
        <CardContent className="p-0 flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by Tag Number or Service..."
              className="pl-9 bg-white"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="outline" className="border-[#003D5C] text-[#003D5C] hover:bg-slate-50">
            Create Logical Tag
          </Button>
        </CardContent>
      </Card>

      <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-50">
            <TableRow>
              <TableHead className="font-bold text-[#003D5C]">Tag Number</TableHead>
              <TableHead className="font-bold text-[#003D5C]">Description</TableHead>
              <TableHead className="font-bold text-[#003D5C]">Area / Service</TableHead>
              <TableHead className="font-bold text-[#003D5C]">Current Mounting</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-10">Loading tags...</TableCell>
              </TableRow>
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-10 text-muted-foreground">
                  No instrument tags found.
                </TableCell>
              </TableRow>
            ) : filtered.map((tag) => {
              const activeInstall = tag.installations?.find((i: any) => i.is_active)

              return (
                <TableRow key={tag.id} className="hover:bg-slate-50/50">
                  <TableCell className="font-bold text-[#FF6B35]">{tag.tag_number}</TableCell>
                  <TableCell className="max-w-xs truncate">{tag.description}</TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">{tag.area}</span>
                      <span className="text-xs text-muted-foreground">{tag.service}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {activeInstall ? (
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded bg-emerald-50 flex items-center justify-center border border-emerald-100">
                          <MapPin className="h-4 w-4 text-emerald-600" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-sm font-mono text-[#003D5C] font-bold">
                            {activeInstall.equipment?.serial_number}
                          </span>
                          <span className="text-[10px] text-emerald-600 font-bold uppercase tracking-tighter">
                            Installed {new Date(activeInstall.installation_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 grayscale group cursor-pointer" onClick={() => {
                        setSelectedTag(tag)
                        setInstallDialogOpen(true)
                      }}>
                        <div className="h-8 w-8 rounded bg-slate-100 flex items-center justify-center border border-dashed border-slate-300 group-hover:border-orange-300">
                          <Plus className="h-4 w-4 text-slate-400 group-hover:text-orange-500" />
                        </div>
                        <span className="text-sm text-slate-400 group-hover:text-orange-500 font-medium italic">Empty - Install now</span>
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-right space-x-1">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="ghost" size="icon" title="History">
                          <History className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Mounting History: {tag.tag_number}</DialogTitle>
                        </DialogHeader>
                        <div className="py-4">
                          {tag.installations?.length > 0 ? (
                            <div className="space-y-4">
                              {tag.installations.map((inst: any) => (
                                <div key={inst.id} className="text-sm border-b pb-2 flex justify-between items-center">
                                  <div>
                                    <p className="font-bold">{inst.equipment?.serial_number}</p>
                                    <p className="text-xs text-muted-foreground">
                                      {new Date(inst.installation_date).toLocaleDateString()} -
                                      {inst.removal_date ? new Date(inst.removal_date).toLocaleDateString() : "Present"}
                                    </p>
                                  </div>
                                  <Badge variant={inst.is_active ? "default" : "secondary"}>
                                    {inst.is_active ? "Active" : "Removed"}
                                  </Badge>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-center text-muted-foreground text-sm">No historical movements recorded yet.</p>
                          )}
                        </div>
                      </DialogContent>
                    </Dialog>

                    {activeInstall ? (
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Remove Equipment"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => handleRemove(tag.id, activeInstall.id)}
                      >
                        <Replace className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Install Equipment"
                        className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                        onClick={() => {
                          setSelectedTag(tag)
                          setInstallDialogOpen(true)
                        }}
                      >
                        <Replace className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      {/* Installation Dialog */}
      <Dialog open={installDialogOpen} onOpenChange={setInstallDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Install Equipment</DialogTitle>
            <DialogDescription>
              Mount a physical device onto tag <strong>{selectedTag?.tag_number}</strong>.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <Label>Available Equipment (S/N)</Label>
              <Select value={selectedEquipmentId} onValueChange={setSelectedEquipmentId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a serial number..." />
                </SelectTrigger>
                <SelectContent>
                  {availableEquipment.length > 0 ? (
                    availableEquipment.map((eq: any) => (
                      <SelectItem key={eq.id} value={eq.id.toString()}>
                        {eq.serial_number} ({eq.model})
                      </SelectItem>
                    ))
                  ) : (
                    <div className="p-2 text-center text-sm text-muted-foreground italic">No equipment available</div>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setInstallDialogOpen(false)}>Cancel</Button>
            <Button
              className="bg-[#FF6B35] hover:bg-[#e05a2b] text-white"
              onClick={handleInstall}
              disabled={submitting || !selectedEquipmentId}
            >
              {submitting ? "Installing..." : "Confirm Installation"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
