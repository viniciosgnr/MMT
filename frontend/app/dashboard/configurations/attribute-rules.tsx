"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Trash2, ShieldCheck, Settings2 } from "lucide-react"

export function AttributeRules() {
  const [attributes] = useState([
    { id: 1, name: "Calibration Interval", type: "Numerical", unit: "Months", rules: "Mandatory, > 0" },
    { id: 2, name: "Uncertainty Limit", type: "Numerical", unit: "%", rules: "< 0.5" },
    { id: 3, name: "Maintenance Strategy", type: "Multiple Choice", unit: "", rules: "Mandatory" },
  ])

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="space-y-1">
            <CardTitle>Dynamic Attribute Definitions</CardTitle>
            <CardDescription>Define custom fields and their validation rules for assets.</CardDescription>
          </div>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" /> New Attribute
          </Button>
        </CardHeader>
        <CardContent>
          <div className="relative overflow-x-auto border rounded-md">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-muted/50">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Rules</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {attributes.map((attr) => (
                  <tr key={attr.id} className="border-b hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3 font-medium">
                      <div className="flex flex-col">
                        <span>{attr.name}</span>
                        <span className="text-xs text-muted-foreground font-normal">{attr.unit}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-primary/10 text-primary text-[10px] font-bold px-2 py-0.5 rounded uppercase">
                        {attr.type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <ShieldCheck className="h-3 w-3 text-green-600" />
                        <span className="text-xs">{attr.rules}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8"><Settings2 className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-orange-50/30 border-orange-100">
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Settings2 className="h-4 w-4 text-orange-600" />
            Rule Configuration Logic
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground">
          Validation rules follow the format specified in the Functional Specification.
          Admins can chain rules with <b>AND/OR</b> logic (e.g., [Value &gt; 0] AND [Mandatory if System Type = Ultrasonic]).
        </CardContent>
      </Card>
    </div>
  )
}
