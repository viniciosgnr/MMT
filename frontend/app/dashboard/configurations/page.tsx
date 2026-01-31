"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

import { HierarchyTree } from "./hierarchy-tree"
import { AttributeRules } from "./attribute-rules"
import { SpecializedConfigs } from "./specialized-configs"
import { PropertyEditor } from "./property-editor"
import { fetchParameters, setParameter } from "@/lib/api"
import { toast } from "sonner"
import { useEffect, useState } from "react"

export default function ConfigurationsPage() {
  const [params, setParams] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<{ id: number; tag: string } | null>(null)

  const loadParams = async () => {
    try {
      const data = await fetchParameters("SEPETIBA")
      setParams(data)
    } catch (error) {
      toast.error("Failed to load parameters")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadParams()
  }, [])

  const getParamValue = (key: string, defaultValue: string) => {
    return params.find(p => p.key === key)?.value || defaultValue
  }

  const handleSaveParam = async (key: string, value: string) => {
    try {
      await setParameter({ key, value, fpso: "SEPETIBA" })
      toast.success("Parameter updated")
      loadParams()
    } catch (error) {
      toast.error("Failed to update parameter")
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Configurations (M11)</h1>
        <p className="text-muted-foreground">System-wide parameters and asset modeling.</p>
      </div>

      <Tabs defaultValue="hierarchy" className="w-full">
        <TabsList className="bg-muted p-1">
          <TabsTrigger value="hierarchy">FPSO Hierarchy</TabsTrigger>
          <TabsTrigger value="attributes">Dynamic Attributes</TabsTrigger>
          <TabsTrigger value="specialized">Specialized</TabsTrigger>
          <TabsTrigger value="frequencies">Frequencies</TabsTrigger>
          <TabsTrigger value="general">System Identity</TabsTrigger>
        </TabsList>

        {/* Hierarchy Management */}
        <TabsContent value="hierarchy" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <HierarchyTree
                selectedId={selectedNode?.id}
                onSelect={(id, tag) => setSelectedNode({ id, tag })}
              />
            </div>
            <div className="space-y-4">
              <PropertyEditor nodeId={selectedNode?.id || null} nodeTag={selectedNode?.tag || null} />

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Modeling Guide</CardTitle>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground space-y-2">
                  <p><b>1. Define FPSO Root:</b> Start with the vessel name.</p>
                  <p><b>2. Add Systems:</b> E.g., Gas Export, Oil Export.</p>
                  <p><b>3. Add Variables:</b> Pressure, Temp, Fluid Properties.</p>
                  <p><b>4. Link Devices:</b> Transmitters and Flow Meters.</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Dynamic Attributes */}
        <TabsContent value="attributes" className="mt-4">
          <AttributeRules />
        </TabsContent>

        {/* Specialized Configurations */}
        <TabsContent value="specialized" className="mt-4">
          <SpecializedConfigs />
        </TabsContent>

        {/* Frequencies */}
        <TabsContent value="frequencies" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Calibration & Maintenance Frequencies</CardTitle>
              <CardDescription>Default periods for recurring tasks configured per FPSO.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Pressure Transmitter Calibration (Months)</Label>
                  <Select
                    value={getParamValue("pt_cal_freq", "12")}
                    onValueChange={(v) => handleSaveParam("pt_cal_freq", v)}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="6">Every 6 Months</SelectItem>
                      <SelectItem value="12">Every 12 Months</SelectItem>
                      <SelectItem value="24">Every 24 Months</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Flow Meter Proving (Months/Interval)</Label>
                  <Select
                    value={getParamValue("flow_meter_proving_freq", "1")}
                    onValueChange={(v) => handleSaveParam("flow_meter_proving_freq", v)}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0.5">Every 2 Weeks</SelectItem>
                      <SelectItem value="1">Monthly</SelectItem>
                      <SelectItem value="3">Quarterly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Sampling Frequency (Days)</Label>
                  <Input
                    type="number"
                    defaultValue={getParamValue("sampling_freq_days", "7")}
                    onBlur={(e) => handleSaveParam("sampling_freq_days", e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* General Parameters */}
        <TabsContent value="general" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Identity</CardTitle>
              <CardDescription>Basic system information and global parameters.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Metering System Name</Label>
                  <Input
                    defaultValue={getParamValue("system_name", "FPSO SEPETIBA Metering")}
                    onBlur={(e) => handleSaveParam("system_name", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Operator Name</Label>
                  <Input
                    defaultValue={getParamValue("operator_name", "SBM Offshore")}
                    onBlur={(e) => handleSaveParam("operator_name", e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
