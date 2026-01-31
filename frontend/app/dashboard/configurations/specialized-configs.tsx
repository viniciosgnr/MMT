"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Trash2, Calendar as CalendarIcon, MapPin, Droplets } from "lucide-react"
import { fetchWells, createWell, fetchHolidays, createHoliday, fetchStockLocations, createStockLocation } from "@/lib/api"
import { toast } from "sonner"
import { format } from "date-fns"

export function SpecializedConfigs() {
  const [wells, setWells] = useState<any[]>([])
  const [holidays, setHolidays] = useState<any[]>([])
  const [stockLocations, setStockLocations] = useState<any[]>([])

  const [loading, setLoading] = useState(true)

  // Form states
  const [newWellTag, setNewWellTag] = useState("")
  const [newHolidayDate, setNewHolidayDate] = useState("")
  const [newHolidayDesc, setNewHolidayDesc] = useState("")
  const [newStockName, setNewStockName] = useState("")

  const loadAll = async () => {
    setLoading(true)
    try {
      const [w, h, s] = await Promise.all([
        fetchWells(),
        fetchHolidays(),
        fetchStockLocations()
      ])
      setWells(Array.isArray(w) ? w : [])
      setHolidays(Array.isArray(h) ? h : [])
      setStockLocations(Array.isArray(s) ? s : [])
    } catch (error) {
      toast.error("Failed to load specialized configurations")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  const handleCreateWell = async () => {
    if (!newWellTag) return
    try {
      await createWell({ tag: newWellTag, description: "", fpso: "SEPETIBA" })
      toast.success("Well added")
      setNewWellTag("")
      loadAll()
    } catch (error) { toast.error("Failed to add well") }
  }

  const handleCreateHoliday = async () => {
    if (!newHolidayDate || !newHolidayDesc) return
    try {
      await createHoliday({ date: new Date(newHolidayDate).toISOString(), description: newHolidayDesc, fpso: "SEPETIBA" })
      toast.success("Holiday added")
      setNewHolidayDate("")
      setNewHolidayDesc("")
      loadAll()
    } catch (error) { toast.error("Failed to add holiday") }
  }

  const handleCreateStock = async () => {
    if (!newStockName) return
    try {
      await createStockLocation({ name: newStockName, description: "", fpso: "SEPETIBA" })
      toast.success("Stock location added")
      setNewStockName("")
      loadAll()
    } catch (error) { toast.error("Failed to add stock location") }
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="wells" className="w-full">
        <TabsList className="bg-muted p-1">
          <TabsTrigger value="wells" className="text-xs">Wells</TabsTrigger>
          <TabsTrigger value="holidays" className="text-xs">Holidays</TabsTrigger>
          <TabsTrigger value="stock" className="text-xs">Stock Locations</TabsTrigger>
        </TabsList>

        <TabsContent value="wells" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-sm">Wells</CardTitle>
                <CardDescription className="text-xs">Define wells associated with this FPSO.</CardDescription>
              </div>
              <div className="flex gap-2">
                <Input placeholder="Well Tag..." value={newWellTag} onChange={(e) => setNewWellTag(e.target.value)} className="h-8 text-xs w-40" />
                <Button size="sm" onClick={handleCreateWell} className="h-8 px-3">
                  <Plus className="h-4 w-4 mr-1" /> Add
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {wells.map(well => (
                  <div key={well.id} className="flex items-center justify-between p-2 border rounded-md bg-muted/5 group">
                    <div className="flex items-center gap-2">
                      <Droplets className="h-3 w-3 text-blue-500" />
                      <span className="text-sm font-medium">{well.tag}</span>
                    </div>
                    <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 text-destructive"><Trash2 className="h-3 w-3" /></Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="holidays" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-sm">Holiday Calendar</CardTitle>
                <CardDescription className="text-xs">Days excluded from SLA and operational counts.</CardDescription>
              </div>
              <div className="flex gap-2">
                <Input type="date" value={newHolidayDate} onChange={(e) => setNewHolidayDate(e.target.value)} className="h-8 text-xs w-36" />
                <Input placeholder="Event Name" value={newHolidayDesc} onChange={(e) => setNewHolidayDesc(e.target.value)} className="h-8 text-xs w-36" />
                <Button size="sm" onClick={handleCreateHoliday} className="h-8 px-3">
                  <Plus className="h-4 w-4 mr-1" /> Add
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {holidays.map(h => (
                  <div key={h.id} className="flex items-center justify-between p-2 border-b last:border-0 group">
                    <div className="flex items-center gap-3">
                      <CalendarIcon className="h-4 w-4 text-orange-500" />
                      <span className="text-xs font-medium">{format(new Date(h.date), "dd MMM yyyy")}</span>
                      <span className="text-xs text-muted-foreground">{h.description}</span>
                    </div>
                    <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 text-destructive"><Trash2 className="h-3 w-3" /></Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stock" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-sm">Stock Locations</CardTitle>
                <CardDescription className="text-xs">Storage points for metering spares and reagents.</CardDescription>
              </div>
              <div className="flex gap-2">
                <Input placeholder="Location Name" value={newStockName} onChange={(e) => setNewStockName(e.target.value)} className="h-8 text-xs w-48" />
                <Button size="sm" onClick={handleCreateStock} className="h-8 px-3">
                  <Plus className="h-4 w-4 mr-1" /> Add
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {stockLocations.map(loc => (
                  <div key={loc.id} className="p-3 border rounded-md bg-muted/5 group relative">
                    <div className="flex items-center gap-2 mb-1">
                      <MapPin className="h-3 w-3 text-red-500" />
                      <span className="text-sm font-bold">{loc.name}</span>
                    </div>
                    <Button variant="ghost" size="icon" className="h-6 w-6 absolute top-1 right-1 opacity-0 group-hover:opacity-100 text-destructive"><Trash2 className="h-3 w-3" /></Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
