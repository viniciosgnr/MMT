"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, CheckCircle2, RefreshCw, Server, AlertTriangle } from "lucide-react"
import { toast } from "sonner"
import { runFCVerificationSimulation } from "@/lib/api"

interface FCVerificationResult {
  tag: string
  parameter: string
  mmt_value: string
  fc_value: string
  status: string
  deviation?: string
}

export function FCVerificationPanel() {
  const [results, setResults] = useState<FCVerificationResult[]>([])
  const [loading, setLoading] = useState(false)
  const [hasRun, setHasRun] = useState(false)

  const handleRunVerification = async () => {
    setLoading(true)
    try {
      const data = await runFCVerificationSimulation()
      setResults(data)
      setHasRun(true)
      toast.success("Flow Computer Verification Check completed.")
    } catch (error) {
      console.error(error)
      toast.error("Failed to connect to Flow Computer Simulation")
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Match":
        return <Badge className="bg-emerald-500 hover:bg-emerald-600"><CheckCircle2 className="w-3 h-3 mr-1" /> Match</Badge>
      case "Warning":
        return <Badge className="bg-amber-500 hover:bg-amber-600"><AlertTriangle className="w-3 h-3 mr-1" /> Warning</Badge>
      case "Critical":
        return <Badge className="bg-red-500 hover:bg-red-600"><AlertCircle className="w-3 h-3 mr-1" /> Critical</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex flex-col gap-2">
              <CardTitle className="text-xl flex items-center gap-2">
                <Server className="h-5 w-5 text-[#003D5C]" />
                Flow Computer Verification (Spec 6.4.11)
              </CardTitle>
              <CardDescription>
                Compare "Approved" MMT Configuration vs "Live" Flow Computer Parameters.
                Detects unauthorized field changes.
              </CardDescription>
            </div>
            <Button
              onClick={handleRunVerification}
              disabled={loading}
              className="bg-[#003D5C] hover:bg-[#002A40]"
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              {loading ? "Scanning Protocols..." : "Run FC Verification"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {!hasRun ? (
            <div className="text-center py-12 text-muted-foreground bg-slate-50 rounded-lg border border-dashed">
              <Server className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Click "Run FC Verification" to poll specific registers and compare values.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tag</TableHead>
                  <TableHead>Parameter</TableHead>
                  <TableHead>MMT (Approved)</TableHead>
                  <TableHead>Flow Computer (Live)</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {results.map((res, index) => (
                  <TableRow key={index} className={res.status === "Critical" ? "bg-red-50" : ""}>
                    <TableCell className="font-semibold">{res.tag}</TableCell>
                    <TableCell>{res.parameter}</TableCell>
                    <TableCell className="font-mono text-xs">{res.mmt_value}</TableCell>
                    <TableCell className="font-mono text-xs">{res.fc_value}</TableCell>
                    <TableCell>{getStatusBadge(res.status)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{res.deviation || "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {hasRun && results.some(r => r.status === "Critical") && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-lg flex gap-4 items-start">
          <AlertCircle className="text-red-600 h-6 w-6 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-bold text-red-900">Critical Discrepancies Detected</h4>
            <p className="text-sm text-red-800">
              Safety-critical parameters in the Flow Computer do not match the approved Configuration.
              Immediate investigation is required. Justification must be provided to acknowledge this state.
            </p>
            <Button variant="destructive" size="sm" className="mt-3">Acknowledge Alert</Button>
          </div>
        </div>
      )}
    </div>
  )
}
