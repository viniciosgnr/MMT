
"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Calculator, Activity } from "lucide-react"

// MVP Mock Data for Uncertainty Budget
// In real world, these come from M2 Certificates + Real-time Inputs
const MOCK_BUDGET = [
  { source: "Differential Pressure", value: "250.0 mbar", u_std: "0.15%", sensitivity: "0.5", contribution: "0.075%" },
  { source: "Static Pressure", value: "85.0 bar", u_std: "0.10%", sensitivity: "0.1", contribution: "0.010%" },
  { source: "Temperature", value: "45.0 °C", u_std: "0.20 °C", sensitivity: "0.8", contribution: "0.080%" },
  { source: "Density", value: "850.0 kg/m³", u_std: "0.30 kg/m³", sensitivity: "1.0", contribution: "0.035%" },
  { source: "Flow Computer (A/D)", value: "-", u_std: "0.05%", sensitivity: "1.0", contribution: "0.050%" },
]

export function UncertaintyVisualizerPanel() {
  const [expandedU, setExpandedU] = useState("0.42%") // Mock calculation

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <CardTitle className="text-xl flex items-center gap-2">
              <Calculator className="h-5 w-5 text-[#003D5C]" />
              System Uncertainty Visualizer (Real-Time)
            </CardTitle>
            <CardDescription>
              Dynamic Uncertainty Budget based on current process conditions (ISO 5167).
            </CardDescription>
          </div>
          <div className="text-right">
            <span className="text-sm text-muted-foreground mr-2">Expanded Uncertainty (k=2):</span>
            <Badge className="text-lg px-3 py-1 bg-[#003D5C] hover:bg-[#002A40]">{expandedU}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Source of Uncertainty</TableHead>
              <TableHead>Process Value</TableHead>
              <TableHead>Std. Uncertainty (u)</TableHead>
              <TableHead>Sensitivity Coeff. (c)</TableHead>
              <TableHead className="text-right">Contribution (u × c)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {MOCK_BUDGET.map((row, index) => (
              <TableRow key={index}>
                <TableCell className="font-medium">{row.source}</TableCell>
                <TableCell>{row.value}</TableCell>
                <TableCell>{row.u_std}</TableCell>
                <TableCell>{row.sensitivity}</TableCell>
                <TableCell className="text-right font-mono">{row.contribution}</TableCell>
              </TableRow>
            ))}
            <TableRow className="bg-slate-50 font-bold border-t-2">
              <TableCell colSpan={4} className="text-right">Combined Standard Uncertainty (uc):</TableCell>
              <TableCell className="text-right">0.21%</TableCell>
            </TableRow>
            <TableRow className="bg-slate-100 font-bold">
              <TableCell colSpan={4} className="text-right">Expanded Uncertainty (U95):</TableCell>
              <TableCell className="text-right text-[#003D5C]">0.42%</TableCell>
            </TableRow>
          </TableBody>
        </Table>
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md flex gap-2 text-sm text-yellow-800">
          <Activity className="h-4 w-4 mt-0.5" />
          <p>
            <strong>Note:</strong> This simulation uses nominal values.
            Real-time integration requires connection to live Flow Computer inputs (via M5).
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
