"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Trash2, Calendar as CalendarIcon, MapPin } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"
import { format } from "date-fns"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export function SpecializedConfigs() {
  const [holidays, setHolidays] = useState<any[]>([])
  const [stockLocations, setStockLocations] = useState<any[]>([])

  const [loading, setLoading] = useState(true)

  // Form states
  const [newHolidayDate, setNewHolidayDate] = useState("")
  const [newHolidayDesc, setNewHolidayDesc] = useState("")
  const [newStockName, setNewStockName] = useState("")

  const loadAll = async () => {
    setLoading(true)
    try {
      const [hRes, sRes] = await Promise.all([
        apiFetch("/config/holidays"),
        apiFetch("/config/stock-locations"),
      ])

      setHolidays(hRes.ok ? await hRes.json() : [])
      setStockLocations(sRes.ok ? await sRes.json() : [])
    } catch (error) {
      toast.error("Failed to load specialized configurations")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  const handleCreateHoliday = async () => {
    if (!newHolidayDate || !newHolidayDesc) return
    try {
      const res = await apiFetch("/config/holidays", {
        method: "POST",
        body: JSON.stringify({ date: new Date(newHolidayDate).toISOString(), description: newHolidayDesc, fpso: "SEPETIBA" })
      })
      if (res.ok) {
        toast.success("Holiday added")
        setNewHolidayDate("")
        setNewHolidayDesc("")
        loadAll()
      } else {
        throw new Error("Failed")
      }
    } catch (error) { toast.error("Failed to add holiday") }
  }

  const handleCreateStock = async () => {
    if (!newStockName) return
    try {
      const res = await apiFetch("/config/stock-locations", {
        method: "POST",
        body: JSON.stringify({ name: newStockName, description: "", fpso: "SEPETIBA" })
      })
      if (res.ok) {
        toast.success("Stock location added")
        setNewStockName("")
        loadAll()
      } else {
        throw new Error("Failed")
      }
    } catch (error) { toast.error("Failed to add stock location") }
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="holidays" className="w-full">
        <TabsList className="bg-muted p-1">
          <TabsTrigger value="holidays" className="text-xs">Holidays</TabsTrigger>
          <TabsTrigger value="stock" className="text-xs">Stock Locations</TabsTrigger>
        </TabsList>


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
