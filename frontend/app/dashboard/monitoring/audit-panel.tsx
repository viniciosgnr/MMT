"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, RefreshCcw, Activity } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"
import { format } from "date-fns"

type AuditResult = {
  rule_id: string
  rule_name: string
  severity: "Critical" | "Warning" | "Info"
  status: "Pass" | "Fail"
  target_system: string
  details: string
  timestamp: string
}

export function AuditPanel() {
  const [results, setResults] = useState<AuditResult[]>([])
  const [loading, setLoading] = useState(false)
  const [hasRun, setHasRun] = useState(false)

  const handleRunAudit = async () => {
    setLoading(true)
    try {
      const response = await apiFetch("/audit/simulate", { method: "POST" })
      if (response.ok) {
        setResults(await response.json())
        setHasRun(true)
        toast.success("Regulatory audit simulation completed successfully.")
      } else {
        throw new Error("Simulation failed")
      }
    } catch (error) {
      console.error(error)
      toast.error("Failed to run audit simulation")
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    return status === "Pass" ? (
      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100 uppercase tracking-widest text-[10px] font-black pl-1 pr-2">
        <CheckCircle2 className="h-3 w-3 mr-1" /> Satisfactory
      </Badge>
    ) : (
      <Badge className="bg-red-50 text-red-700 border-red-200 hover:bg-red-100 uppercase tracking-widest text-[10px] font-black pl-1 pr-2">
        <XCircle className="h-3 w-3 mr-1" /> Attention
      </Badge>
    )
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "Critical": return <AlertTriangle className="h-4 w-4 text-red-500" />
      case "Warning": return <Activity className="h-4 w-4 text-amber-500" />
      default: return <ShieldCheck className="h-4 w-4 text-blue-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-black text-[#003D5C] flex items-center gap-2">
            <ShieldCheck className="h-5 w-5" /> Regulatory Compliance Audit (Spec 6.8.1)
          </h3>
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            Cross-check Configuration (M11) vs Live Data (M5) vs Certificates (M2)
          </p>
        </div>
        <Button
          onClick={handleRunAudit}
          disabled={loading}
          className="bg-[#FF6B35] hover:bg-[#e55a2b] text-white font-black text-xs uppercase tracking-widest rounded-full px-6 shadow-md transition-all"
        >
          {loading ? (
            <><RefreshCcw className="mr-2 h-4 w-4 animate-spin" /> Audit Running...</>
          ) : (
            <><Activity className="mr-2 h-4 w-4" /> Run System Audit</>
          )}
        </Button>
      </div>

      {!hasRun ? (
        <Card className="border-dashed border-2 border-slate-200 bg-slate-50">
          <CardContent className="flex flex-col items-center justify-center py-16 text-slate-400">
            <ShieldCheck className="h-16 w-16 mb-4 opacity-10" />
            <h4 className="font-black text-lg text-[#003D5C]">Audit System Ready</h4>
            <p className="text-sm font-medium mb-4">Click "Run System Audit" to verify 10+ regulatory checkpoints.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="border-l-4 border-l-emerald-500 shadow-sm">
              <CardContent className="pt-6">
                <div className="text-2xl font-black text-emerald-600">{results.filter(r => r.status === "Pass").length}</div>
                <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Checks Passed</div>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-red-500 shadow-sm">
              <CardContent className="pt-6">
                <div className="text-2xl font-black text-red-600">{results.filter(r => r.status === "Fail" && r.severity === "Critical").length}</div>
                <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Critical Failures</div>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-amber-500 shadow-sm">
              <CardContent className="pt-6">
                <div className="text-2xl font-black text-amber-500">{results.filter(r => r.status === "Fail" && r.severity === "Warning").length}</div>
                <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Warnings</div>
              </CardContent>
            </Card>
          </div>

          <Card className="shadow-sm border-slate-200">
            <CardHeader className="bg-slate-50 border-b pb-3">
              <CardTitle className="text-sm font-black text-[#003D5C] uppercase tracking-widest">Audit Detailed Report</CardTitle>
              <CardDescription className="text-xs font-bold text-slate-400">Generated on {format(new Date(), "dd/MM/yyyy 'at' HH:mm:ss")}</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]"></TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Rule ID</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Check Name</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Target System</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Result Status</TableHead>
                    <TableHead className="text-[10px] font-black uppercase tracking-widest text-[#003D5C]">Analysis Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((r, i) => (
                    <TableRow key={i} className="hover:bg-slate-50/50">
                      <TableCell>{getSeverityIcon(r.severity)}</TableCell>
                      <TableCell className="font-mono text-xs text-slate-500 font-bold">{r.rule_id}</TableCell>
                      <TableCell className="font-bold text-xs text-[#003D5C]">{r.rule_name}</TableCell>
                      <TableCell className="font-bold text-xs text-[#FF6B35]">{r.target_system}</TableCell>
                      <TableCell>{getStatusBadge(r.status)}</TableCell>
                      <TableCell className="text-xs font-medium text-slate-600 line-clamp-2" title={r.details}>
                        {r.details}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
