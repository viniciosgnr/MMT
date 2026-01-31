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
import { ChevronLeft, ChevronRight, Database } from "lucide-react"
import Link from "next/link"
import Image from "next/image"

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)

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
          <Database className="h-5 w-5 text-[#FF6B35]" />
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
                {/* FPSO MARICÁ */}
                <AccordionItem value="fpso-marica" className="border-none">
                  <AccordionTrigger className="py-2 px-3 hover:bg-slate-50 rounded-md hover:no-underline text-xs font-bold text-[#003D5C]">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-amber-500" />
                      FPSO MARICÁ
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="pl-4 pb-0">
                    <Accordion type="multiple" className="w-full">
                      {/* Run 1 */}
                      <AccordionItem value="run-1" className="border-none">
                        <AccordionTrigger className="py-1.5 px-3 hover:bg-slate-50 rounded-sm hover:no-underline text-[10px] font-bold text-slate-700">
                          Oil Rundown Run 1 – T62-FT-1103
                        </AccordionTrigger>
                        <AccordionContent className="pl-4 pb-2 space-y-3 mt-1 border-l border-slate-100 ml-2">
                          {/* Pressure */}
                          <div>
                            <p className="text-[9px] font-bold text-[#FF6B35] uppercase tracking-tighter mb-1">Pressure</p>
                            <div className="pl-2 space-y-1">
                              <button className="text-[10px] text-slate-500 hover:text-[#003D5C] block w-full text-left py-0.5">T62-PT-1103</button>
                            </div>
                          </div>
                          {/* Temperature */}
                          <div>
                            <p className="text-[9px] font-bold text-[#FF6B35] uppercase tracking-tighter mb-1">Temperature</p>
                            <div className="pl-2 space-y-1">
                              <button className="text-[10px] text-slate-500 hover:text-[#003D5C] block w-full text-left py-0.5">T62-TT-1103</button>
                              <button className="text-[10px] text-slate-500 hover:text-[#003D5C] block w-full text-left py-0.5">T62-TE-1103</button>
                            </div>
                          </div>
                          {/* Fluid Properties */}
                          <div>
                            <p className="text-[9px] font-bold text-[#FF6B35] uppercase tracking-tighter mb-1">Fluid Properties</p>
                            <div className="pl-2 space-y-1">
                              <button className="text-[10px] text-slate-500 hover:text-[#003D5C] block w-full text-left py-0.5">T62-AP-1111</button>
                              <button className="text-[10px] text-slate-500 hover:text-[#003D5C] block w-full text-left py-0.5">T62-AP-1112</button>
                              <button className="text-[10px] text-slate-500 hover:text-[#003D5C] block w-full text-left py-0.5">T62-AT-1112</button>
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>

                      {/* Run 2 */}
                      <AccordionItem value="run-2" className="border-none">
                        <AccordionTrigger className="py-1.5 px-3 hover:bg-slate-50 rounded-sm hover:no-underline text-[10px] font-bold text-slate-700">
                          Oil Rundown Run 2 – T62-FT-1108
                        </AccordionTrigger>
                        <AccordionContent className="pl-4 pb-2 space-y-2 mt-1 border-l border-slate-100 ml-2">
                          <div>
                            <p className="text-[9px] font-bold text-[#FF6B35] uppercase tracking-tighter mb-1">Fluid Properties</p>
                            <div className="pl-2 space-y-1">
                              <button className="text-[10px] text-slate-500 hover:text-[#003D5C] block w-full text-left py-0.5">T62-AP-1111</button>
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </AccordionContent>
                </AccordionItem>

                {/* FPSO SAQUAREMA */}
                <AccordionItem value="fpso-saquarema" className="border-none">
                  <AccordionTrigger className="py-2 px-3 hover:bg-slate-50 rounded-md hover:no-underline text-xs font-bold text-[#003D5C]">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                      FPSO SAQUAREMA
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="pl-6 py-2 text-[10px] text-slate-400 italic">
                    Subsystems structure pending.
                  </AccordionContent>
                </AccordionItem>

                {/* FPSO SEPETIBA */}
                <AccordionItem value="fpso-sepetiba" className="border-none">
                  <AccordionTrigger className="py-2 px-3 hover:bg-slate-50 rounded-md hover:no-underline text-xs font-bold text-[#003D5C]">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      FPSO SEPETIBA
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="pl-6 py-2 text-[10px] text-slate-400 italic">
                    Subsystems structure pending.
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className={cn(
        "p-4 border-t bg-slate-50/50",
        isCollapsed && "flex items-center justify-center px-2"
      )}>
        <div className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity">
          <div className="h-10 w-10 rounded-full bg-white border-2 border-[#FF6B35] overflow-hidden flex-shrink-0">
            <Image src="/user-avatar.png" alt="User" width={40} height={40} className="object-cover" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-bold text-[#003D5C] truncate">Daniel Bernoulli</span>
              <span className="text-[10px] text-slate-500 font-medium truncate uppercase tracking-tighter">Senior Metering Engineer</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
