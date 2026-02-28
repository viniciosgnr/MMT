"use client"

import React, { useState } from "react"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { ChevronLeft, ChevronRight, Database, LogOut, Ship } from "lucide-react"
import Link from "next/link"
import Image from "next/image"
import { useRouter, usePathname } from "next/navigation"
import { createClient } from "@/utils/supabase/client"
import { apiFetch } from "@/lib/api"

interface Node {
  id: number
  tag: string
  description?: string
  level_type: string
  attributes?: Record<string, any>
  children?: Node[]
}

const fpsoColors: Record<string, string> = {
  "FPSO MARICÁ": "bg-amber-500",
  "FPSO SAQUAREMA": "bg-blue-500",
  "FPSO SEPETIBA": "bg-emerald-500",
}

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [treeData, setTreeData] = useState<Node[]>([])
  const router = useRouter()
  const pathname = usePathname()
  const supabase = createClient()

  React.useEffect(() => {
    async function load() {
      try {
        const res = await apiFetch(`/config/hierarchy/tree?_t=${Date.now()}`)
        if (res.ok) setTreeData(await res.json())
      } catch (err) {
        console.error("Failed to load sidebar tree", err)
      }
    }
    load()

    window.addEventListener("hierarchy-updated", load)
    return () => window.removeEventListener("hierarchy-updated", load)
  }, [])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push("/login")
    router.refresh()
  }

  const handleNodeClick = (nodeId: number) => {
    // Navigate to M11 module and select the exact node in the tree
    router.push(`/dashboard/configurations?nodeId=${nodeId}`)
  }

  return (
    <aside className={cn(
      "h-full border-r bg-white flex flex-col transition-all duration-300 relative z-40 shadow-sm",
      isCollapsed ? "w-16" : "w-72"
    )}>
      {/* Sidebar Toggle Button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-3 top-20 h-6 w-6 rounded-full border bg-white shadow-sm z-50 hover:bg-[#FF6B35] hover:text-white transition-colors"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </Button>

      <div className={cn(
        "p-5 border-b flex flex-col gap-2 bg-[#003D5C] text-white",
        isCollapsed && "items-center px-2"
      )}>
        <div className="flex items-center gap-3">
          <Ship className="h-5 w-5 text-[#FF6B35]" />
          {!isCollapsed && <h2 className="font-bold tracking-tight text-lg">FPSO Tree</h2>}
        </div>
        {!isCollapsed && <p className="text-[10px] text-white/60 font-medium uppercase tracking-widest">Hierarchy Browser</p>}
      </div>

      <ScrollArea className="flex-1">
        <div className={cn("p-4", isCollapsed && "px-2 items-center flex flex-col gap-4")}>
          {isCollapsed ? (
            <div className="flex flex-col gap-6 pt-4 text-[#003D5C]">
              <Database className="h-6 w-6 cursor-pointer hover:text-[#FF6B35] transition-colors" />
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-2">Production Units</p>
              <Accordion type="single" collapsible className="w-full">
                {treeData.map((fpso) => (
                  <AccordionItem key={fpso.id} value={`fpso-${fpso.id}`} className="border-none">
                    <AccordionTrigger
                      className="py-2 px-3 hover:bg-slate-50 rounded-md hover:no-underline text-xs font-bold text-[#003D5C]"
                    >
                      <div className="flex items-center gap-2">
                        <span className={cn("w-2 h-2 rounded-full", fpsoColors[fpso.tag] || "bg-slate-500")} />
                        {fpso.tag}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pl-4 pb-0">
                      {(!fpso.children || fpso.children.length === 0) ? (
                        <div className="pl-6 py-2 text-[10px] text-slate-400 italic">Subsystems structure pending.</div>
                      ) : (
                        <Accordion type="multiple" className="w-full">
                          {fpso.children.map(meter => {
                            const samplePoints = meter.children || []

                            return (
                              <AccordionItem key={meter.id} value={`meter-${meter.id}`} className="border-none">
                                <AccordionTrigger
                                  className="py-1.5 px-3 hover:bg-slate-50 rounded-sm hover:no-underline text-[10px] font-bold text-slate-700 text-left"
                                >
                                  {meter.description} {meter.tag ? `– ${meter.tag}` : ''}
                                </AccordionTrigger>
                                <AccordionContent className="pl-4 pb-2 space-y-3 mt-1 border-l border-slate-100 ml-2">
                                  {/* Allow clicking on the Metering Point itself */}
                                  <button
                                    onClick={() => handleNodeClick(meter.id)}
                                    className="text-[10px] font-semibold text-indigo-600 hover:text-indigo-800 block w-full text-left py-0.5"
                                  >
                                    Inspect Metering Point
                                  </button>

                                  {samplePoints.length > 0 && (
                                    <div>
                                      <p className="text-[9px] font-bold text-[#FF6B35] uppercase tracking-tighter mb-1 mt-2">FLUID PROPERTIES</p>
                                      <div className="pl-2 space-y-1">
                                        {samplePoints.map(sp => (
                                          <div
                                            key={sp.id}
                                            className="text-[10px] text-slate-500 block w-full text-left py-0.5"
                                          >
                                            {sp.tag}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </AccordionContent>
                              </AccordionItem>
                            )
                          })}
                        </Accordion>
                      )}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className={cn(
        "p-4 border-t bg-slate-50/50",
        isCollapsed && "flex items-center justify-center px-2"
      )}>
        <div className="flex items-center gap-3 w-full">
          <div className="h-10 w-10 rounded-full bg-white border-2 border-[#FF6B35] overflow-hidden flex-shrink-0">
            <Image src="/user-avatar.png" alt="User" width={40} height={40} className="object-cover" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-sm font-bold text-[#003D5C] truncate">Daniel Bernoulli</span>
              <span className="text-[10px] text-slate-500 font-medium truncate uppercase tracking-tighter">Senior Metering Engineer</span>
            </div>
          )}
          {!isCollapsed && (
            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-red-600 hover:bg-red-50" onClick={handleLogout} title="Sign Out">
              <LogOut className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </aside>
  )
}
