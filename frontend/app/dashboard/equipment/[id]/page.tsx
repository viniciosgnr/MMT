"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { apiFetch } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Activity, Wrench, AlertTriangle, FileText, Calendar } from "lucide-react"

export default function EquipmentDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const equipmentId = params.id as string

  const [equipment, setEquipment] = useState<any>(null)
  const [calibrations, setCalibrations] = useState<any[]>([])
  const [maintenanceCards, setMaintenanceCardsCards] = useState<any[]>([])
  const [failures, setFailures] = useState<any[]>([])
  const [samples, setSamples] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!equipmentId) return

    async function fetchData() {
      try {
        setLoading(true)
        // 1. Fetch Equipment Details
        const eqRes = await apiFetch(`/equipment/${equipmentId}`)
        if (eqRes.ok) {
          const eqData = await eqRes.json()
          setEquipment(eqData)
        } else {
          // Handle 404
          console.error("Equipment not found")
        }

        // 2. Fetch Related Data (Parallel)
        const [calRes, maintRes, failRes, sampRes] = await Promise.all([
          apiFetch(`/calibration/tasks?equipment_id=${equipmentId}`),
          apiFetch(`/maintenance/cards?equipment_id=${equipmentId}`),
          apiFetch(`/failures?equipment_id=${equipmentId}`),
          apiFetch(`/chemical/samples?equipment_id=${equipmentId}`)
        ])

        if (calRes.ok) setCalibrations(await calRes.json())
        if (maintRes.ok) setMaintenanceCardsCards(await maintRes.json())
        if (failRes.ok) setFailures(await failRes.json())
        if (sampRes.ok) setSamples(await sampRes.json())

      } catch (error) {
        console.error("Error fetching details:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [equipmentId])

  if (loading) return <div className="p-8">Loading equipment details...</div>
  if (!equipment) return <div className="p-8">Equipment not found.</div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#003D5C]">
            {equipment.serial_number}
          </h1>
          <p className="text-muted-foreground flex items-center gap-2">
            {equipment.model} • {equipment.manufacturer}
            <Badge variant={equipment.status === "Active" ? "default" : "secondary"}>
              {equipment.status}
            </Badge>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Details Card */}
        <Card className="md:col-span-1 h-fit">
          <CardHeader>
            <CardTitle>Specifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <span className="text-sm font-medium text-gray-500">Type</span>
              <p>{equipment.equipment_type}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-500">System</span>
              <p>{equipment.installations?.[0]?.tag?.tag_number || "Uninstalled"}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-500">Calibration Freq.</span>
              <p>{equipment.calibration_frequency_months ? `${equipment.calibration_frequency_months} Months` : "N/A"}</p>
            </div>
          </CardContent>
        </Card>

        {/* Integration Hub Tabs */}
        <div className="md:col-span-2">
          <Tabs defaultValue="calibration" className="w-full">
            <TabsList className="bg-slate-100 w-full justify-start overflow-x-auto">
              <TabsTrigger value="calibration"><Activity className="mr-2 h-4 w-4" /> Calibration (M2)</TabsTrigger>
              <TabsTrigger value="chemical"><FileText className="mr-2 h-4 w-4" /> Chemical (M3)</TabsTrigger>
              <TabsTrigger value="maintenance"><Wrench className="mr-2 h-4 w-4" /> Maintenance (M4)</TabsTrigger>
              <TabsTrigger value="failures"><AlertTriangle className="mr-2 h-4 w-4" /> Failures (M9)</TabsTrigger>
              <TabsTrigger value="docs"><FileText className="mr-2 h-4 w-4" /> Documents</TabsTrigger>
            </TabsList>

            {/* M2 Content */}
            <TabsContent value="calibration" className="space-y-4 mt-4">
              <div className="grid gap-2">
                {calibrations.length === 0 ? <div className="text-muted-foreground p-4">No calibration history found.</div> :
                  calibrations.map((c) => (
                    <Card key={c.id} className="p-4 flex justify-between items-center hover:bg-slate-50">
                      <div>
                        <p className="font-semibold">{c.tag || "Unknown Tag"}</p>
                        <p className="text-sm text-gray-500">Due: {c.due_date}</p>
                      </div>
                      <div className="flex gap-2 items-center">
                        <Badge variant={c.status === "Executed" ? "outline" : "default"}>{c.status}</Badge>
                        <Button size="sm" variant="ghost" onClick={() => router.push(`/dashboard/calibration/tasks/${c.id}`)}>View</Button>
                      </div>
                    </Card>
                  ))}
              </div>
            </TabsContent>

            {/* M3 Content */}
            <TabsContent value="chemical" className="space-y-4 mt-4">
              <div className="bg-blue-50 p-4 rounded-md text-sm text-blue-700 mb-2">
                Showing analyses for Sample Point linked to the currently installed tag.
              </div>
              <div className="grid gap-2">
                {samples.length === 0 ? <div className="text-muted-foreground p-4">No chemical analysis history found for current location.</div> :
                  samples.map((s) => (
                    <Card key={s.id} className="p-4 flex justify-between items-center hover:bg-slate-50">
                      <div>
                        <p className="font-semibold">{s.sample_id}</p>
                        <p className="text-sm text-gray-500">Sampled: {s.sampling_date || "Pending"}</p>
                      </div>
                      <div className="flex gap-2 items-center">
                        <Badge variant="outline">{s.status}</Badge>
                        {s.validation_status && <Badge className={s.validation_status === "Approved" ? "bg-green-500" : "bg-red-500"}>{s.validation_status}</Badge>}
                      </div>
                    </Card>
                  ))}
              </div>
            </TabsContent>

            {/* M4 Content */}
            <TabsContent value="maintenance" className="space-y-4 mt-4">
              <div className="grid gap-2">
                {maintenanceCards.length === 0 ? <div className="text-muted-foreground p-4">No maintenance cards found.</div> :
                  maintenanceCards.map((c) => (
                    <Card key={c.id} className="p-4 flex justify-between items-center hover:bg-slate-50">
                      <div>
                        <p className="font-semibold">{c.title}</p>
                        <p className="text-sm text-gray-500">{c.description}</p>
                      </div>
                      <div className="flex gap-2 items-center">
                        <Badge variant="secondary">{c.column?.name || "Kanban"}</Badge>
                      </div>
                    </Card>
                  ))}
              </div>
            </TabsContent>

            {/* M9 Content */}
            <TabsContent value="failures" className="space-y-4 mt-4">
              <div className="grid gap-2">
                {failures.length === 0 ? <div className="text-muted-foreground p-4">No failure notifications found.</div> :
                  failures.map((f) => (
                    <Card key={f.id} className="p-4 border-red-100 bg-red-50/50 flex justify-between items-center">
                      <div>
                        <p className="font-semibold text-red-700">{f.description?.substring(0, 50)}...</p>
                        <p className="text-sm text-red-500">{f.failure_date}</p>
                      </div>
                      <Badge variant="destructive">{f.status}</Badge>
                    </Card>
                  ))}
              </div>
            </TabsContent>

            {/* Documents Content */}
            <TabsContent value="docs" className="space-y-4 mt-4">
              <p className="text-muted-foreground p-4">Certificates and Manuals section (Placeholder).</p>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}
