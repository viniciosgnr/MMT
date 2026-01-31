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

export default function ConfigurationsPage() {
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
          <TabsTrigger value="frequencies">Frequencies</TabsTrigger>
          <TabsTrigger value="general">System Identity</TabsTrigger>
        </TabsList>

        {/* Hierarchy Management */}
        <TabsContent value="hierarchy" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <HierarchyTree />
            </div>
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Modeling Guide</CardTitle>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground space-y-2">
                  <p><b>1. Define FPSO Root:</b> Start with the vessel name.</p>
                  <p><b>2. Add Systems:</b> E.g., Gas Export, Oil Export.</p>
                  <p><b>3. Add Variables:</b> Pressure, Temp, Flow.</p>
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

        {/* Frequencies */}
        <TabsContent value="frequencies" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Calibration & Maintenance Frequencies</CardTitle>
              <CardDescription>Default periods for recurring tasks configured per FPSO.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Pressure Transmitter Calibration</Label>
                  <Select defaultValue="12">
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="6">Every 6 Months</SelectItem>
                      <SelectItem value="12">Every 12 Months</SelectItem>
                      <SelectItem value="24">Every 24 Months</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Flow Meter Proving</Label>
                  <Select defaultValue="1">
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0.5">Every 2 Weeks</SelectItem>
                      <SelectItem value="1">Monthly</SelectItem>
                      <SelectItem value="3">Quarterly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button>Save Configuration</Button>
            </CardFooter>
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
                  <Input defaultValue="FPSO SEPETIBA Metering" />
                </div>
                <div className="space-y-2">
                  <Label>Operator Name</Label>
                  <Input defaultValue="SBM Offshore" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
