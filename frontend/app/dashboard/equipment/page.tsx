"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Package, Hash, FileDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import EquipmentInventory from "./equipment-inventory"
import TagRegister from "./tag-register"
import { InstallationWizard } from "./installation-wizard"

export default function ManagingEquipmentPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <h1 className="text-2xl font-bold tracking-tight text-[#003D5C]">Managing Equipment (M1)</h1>
          <p className="text-muted-foreground">Manage physical lifecycle (Serial Numbers) and logical locations (Instrument Tags).</p>
        </div>
        <div className="flex gap-2">
          <InstallationWizard onSuccess={() => window.location.reload()} />
          <Button variant="outline" className="border-slate-200">
            <FileDown className="mr-2 h-4 w-4" /> Reports
          </Button>
        </div>
      </div>

      <Tabs defaultValue="inventory" className="w-full space-y-6">
        <TabsList className="bg-slate-100 p-1 border">
          <TabsTrigger
            value="inventory"
            className="data-[state=active]:bg-white data-[state=active]:text-[#FF6B35] data-[state=active]:shadow-sm px-6 py-2"
          >
            <Package className="mr-2 h-4 w-4" /> Physical Inventory
          </TabsTrigger>
          <TabsTrigger
            value="tags"
            className="data-[state=active]:bg-white data-[state=active]:text-[#FF6B35] data-[state=active]:shadow-sm px-6 py-2"
          >
            <Hash className="mr-2 h-4 w-4" /> Instrument Tags
          </TabsTrigger>
        </TabsList>

        <TabsContent value="inventory" className="space-y-4 outline-none">
          <EquipmentInventory />
        </TabsContent>

        <TabsContent value="tags" className="space-y-4 outline-none">
          <TagRegister />
        </TabsContent>
      </Tabs>
    </div>
  )
}
