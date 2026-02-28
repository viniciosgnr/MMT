"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, Trash2, Edit } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export function WellsConfig() {
  const [wells, setWells] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const [newWellFPSO, setNewWellFPSO] = useState("FPSO CIDADE DE ILHABELA (CDI)")

  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingWell, setEditingWell] = useState<any>(null)

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [newWellData, setNewWellData] = useState<any>({
    tag: "", fpso: "FPSO CIDADE DE ILHABELA (CDI)", anp_code: "", sbm_code: "", sample_point_gas: "T71-AP-0602", sample_point_oil: "T62-AP-2224", status: "Active"
  })

  const loadWells = async () => {
    setLoading(true)
    try {
      const res = await apiFetch("/config/wells")
      setWells(res.ok ? await res.json() : [])
    } catch (error) {
      toast.error("Failed to load wells")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWells()
  }, [])

  const handleCreateWell = async () => {
    if (!newWellData.tag || !newWellData.fpso) return
    try {
      const res = await apiFetch("/config/wells", {
        method: "POST",
        body: JSON.stringify(newWellData)
      })
      if (res.ok) {
        toast.success("Well added")
        setIsAddDialogOpen(false)
        setNewWellData({
          tag: "", fpso: newWellFPSO, anp_code: "", sbm_code: "", sample_point_gas: "T71-AP-0602", sample_point_oil: "T62-AP-2224", status: "Active"
        })
        loadWells()
      } else {
        throw new Error("Failed")
      }
    } catch (error) { toast.error("Failed to add well") }
  }

  const handleUpdateWell = async () => {
    if (!editingWell) return
    try {
      const res = await apiFetch(`/config/wells/${editingWell.id}`, {
        method: "PUT",
        body: JSON.stringify(editingWell)
      })
      if (res.ok) {
        toast.success("Well updated successfully")
        setIsEditDialogOpen(false)
        setEditingWell(null)
        loadWells()
      } else {
        throw new Error("Failed to update well")
      }
    } catch (error) { toast.error("Error updating well") }
  }

  const handleDeleteWell = async (id: number) => {
    try {
      const res = await apiFetch(`/config/wells/${id}`, { method: "DELETE" })
      if (res.ok) {
        toast.success("Well deleted")
        loadWells()
      } else { throw new Error("Failed to delete") }
    } catch (error) { toast.error("Error deleting well") }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="text-sm">Wells</CardTitle>
            <CardDescription className="text-xs">Manage wells associated with their respective FPSO. Ensure correct Sample Points and Models.</CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={newWellFPSO} onValueChange={(val) => {
              setNewWellFPSO(val)
              setNewWellData((prev: any) => ({ ...prev, fpso: val }))
            }}>
              <SelectTrigger className="h-8 text-xs w-[180px]">
                <SelectValue placeholder="Select FPSO" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FPSO CIDADE DE ILHABELA (CDI)">CDI</SelectItem>
                <SelectItem value="SEPETIBA">SEPETIBA</SelectItem>
              </SelectContent>
            </Select>
            <Button size="sm" onClick={() => setIsAddDialogOpen(true)} className="h-8 px-3">
              <Plus className="h-4 w-4 mr-1" /> Add
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Tag</TableHead>
                  <TableHead>FPSO</TableHead>
                  <TableHead>ANP Code</TableHead>
                  <TableHead>SBM Code</TableHead>
                  <TableHead>SP Gas</TableHead>
                  <TableHead>SP Oil</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[100px] text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {wells.filter(w => w.fpso === newWellFPSO).map(well => (
                  <TableRow key={well.id}>
                    <TableCell className="font-medium">{well.tag}</TableCell>
                    <TableCell>{well.fpso}</TableCell>
                    <TableCell>{well.anp_code || "-"}</TableCell>
                    <TableCell>{well.sbm_code || "-"}</TableCell>
                    <TableCell>{well.sample_point_gas || "-"}</TableCell>
                    <TableCell>{well.sample_point_oil || "-"}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-full text-[10px] font-medium ${(
                        {
                          "Active": "bg-green-100 text-green-800",
                          "Inactive": "bg-red-100 text-red-800"
                        } as Record<string, string>
                      )[String(well.status)] || "bg-blue-100 text-blue-800"}`}>
                        {well.status || "Active"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary" onClick={() => {
                          setEditingWell({ ...well })
                          setIsEditDialogOpen(true)
                        }}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => handleDeleteWell(well.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {wells.filter(w => w.fpso === newWellFPSO).length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-muted-foreground h-24">No wells found.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Well Details</DialogTitle>
          </DialogHeader>
          {editingWell && (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">Tag</Label>
                <Input value={editingWell.tag} className="col-span-3" readOnly disabled />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">FPSO</Label>
                <Input value={editingWell.fpso} className="col-span-3" readOnly disabled />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">ANP Code</Label>
                <Input value={editingWell.anp_code || ""} onChange={(e) => setEditingWell({ ...editingWell, anp_code: e.target.value })} className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">SBM Code</Label>
                <Input value={editingWell.sbm_code || ""} onChange={(e) => setEditingWell({ ...editingWell, sbm_code: e.target.value })} className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">SP Gas</Label>
                <Select value={editingWell.sample_point_gas || ""} onValueChange={(val) => setEditingWell({ ...editingWell, sample_point_gas: val })}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="Select Gas Point" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="T71-AP-0602">T71-AP-0602</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">SP Oil</Label>
                <Select value={editingWell.sample_point_oil || ""} onValueChange={(val) => setEditingWell({ ...editingWell, sample_point_oil: val })}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="Select Oil Point" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="T62-AP-2224">T62-AP-2224</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">Status</Label>
                <Select value={editingWell.status || "Active"} onValueChange={(val) => setEditingWell({ ...editingWell, status: val })}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Active">Active</SelectItem>
                    <SelectItem value="Inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateWell}>Save changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Well</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">Tag</Label>
              <Input
                value={newWellData.tag}
                onChange={(e) => {
                  const val = e.target.value;
                  let anp = newWellData.anp_code;
                  let sbm = newWellData.sbm_code;

                  const regex = /Poço\s+([A-Z0-9\-]+)\s*\((P-\d+)\)/i;
                  const match = val.match(regex);
                  if (match) {
                    anp = match[1];
                    sbm = match[2];
                  }

                  setNewWellData({
                    ...newWellData,
                    tag: val,
                    anp_code: anp,
                    sbm_code: sbm
                  });
                }}
                className="col-span-3"
                placeholder="e.g. Poço SPH-15 (P-01)"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">FPSO</Label>
              <Input value={newWellData.fpso} className="col-span-3" readOnly disabled />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">ANP Code</Label>
              <Input value={newWellData.anp_code} onChange={(e) => setNewWellData({ ...newWellData, anp_code: e.target.value })} className="col-span-3" />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">SBM Code</Label>
              <Input value={newWellData.sbm_code} onChange={(e) => setNewWellData({ ...newWellData, sbm_code: e.target.value })} className="col-span-3" />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">SP Gas</Label>
              <Select value={newWellData.sample_point_gas} onValueChange={(val) => setNewWellData({ ...newWellData, sample_point_gas: val })}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select Gas Point" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="T71-AP-0602">T71-AP-0602</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">SP Oil</Label>
              <Select value={newWellData.sample_point_oil} onValueChange={(val) => setNewWellData({ ...newWellData, sample_point_oil: val })}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select Oil Point" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="T62-AP-2224">T62-AP-2224</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">Status</Label>
              <Select value={newWellData.status} onValueChange={(val) => setNewWellData({ ...newWellData, status: val })}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Active">Active</SelectItem>
                  <SelectItem value="Inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateWell}>Add Well</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
