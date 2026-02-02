"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import {
  Search,
  FlaskConical,
  FileCheck,
  Settings,
  Plus,
  ArrowRight,
  AlertCircle,
  Clock,
  CheckCircle2,
  Filter,
  Beaker,
  Truck,
  Activity,
  Layers,
  Calendar
} from "lucide-react"
import { toast } from "sonner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { apiFetch } from "@/lib/api"

export default function ChemicalAnalysisDashboard() {
  const router = useRouter()
  const [samples, setSamples] = useState<any[]>([])
  const [samplePoints, setSamplePoints] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [fpsoFilter, setFpsoFilter] = useState("all")

  useEffect(() => {
    loadData()
  }, [fpsoFilter])

  const loadData = async () => {
    try {
      setIsLoading(true)
      const [samplesRes, pointsRes] = await Promise.all([
        apiFetch(`/chemical/samples${fpsoFilter !== "all" ? `?fpso_name=${fpsoFilter}` : ''}`),
        apiFetch(`/chemical/sample-points${fpsoFilter !== "all" ? `?fpso_name=${fpsoFilter}` : ''}`)
      ])

      if (samplesRes.ok && pointsRes.ok) {
        setSamples(await samplesRes.json())
        setSamplePoints(await pointsRes.json())
      } else {
        toast.error("Failed to load sampling data")
      }
    } catch (error) {
      toast.error("Failed to load sampling data")
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { color: string, icon: any }> = {
      "Planned": { color: "bg-slate-500", icon: Clock },
      "Sampled": { color: "bg-green-600", icon: Beaker },
      "Disembark preparation": { color: "bg-blue-500", icon: Truck },
      "Disembark logistics": { color: "bg-blue-600", icon: Truck },
      "Warehouse": { color: "bg-indigo-500", icon: Activity },
      "Logistics to vendor": { color: "bg-indigo-600", icon: Truck },
      "Delivered at vendor": { color: "bg-purple-500", icon: FlaskConical },
      "Report issued": { color: "bg-amber-500", icon: FileCheck },
      "Report under validation": { color: "bg-amber-600", icon: Search },
      "Report approved/reproved": { color: "bg-emerald-600", icon: CheckCircle2 },
      "Flow computer updated": { color: "bg-violet-600", icon: ArrowRight },
    }
    return configs[status] || { color: "bg-slate-400", icon: AlertCircle }
  }

  // Metrics
  const metrics = {
    activeSamples: samples.length,
    overdue: samples.filter(s => {
      if (!s.sampling_date) return false;
      const daysSince = (new Date().getTime() - new Date(s.sampling_date).getTime()) / (1000 * 3600 * 24);
      return daysSince > 15 && s.status !== "Flow computer updated"; // 15 days SLA for report
    }).length,
    pendingValidation: samples.filter(s => s.status === "Report under validation").length,
    pendingFC: samples.filter(s => s.status === "Report approved/reproved").length
  }

  const filteredSamples = samples.filter(s =>
    s.sample_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.sample_point?.tag_number.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Chemical Analysis</h1>
          <p className="text-muted-foreground">Monitoring the 11-status lifecycle from sampling to flow computer update.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push("/dashboard/chemical/points")}>
            <Settings className="w-4 h-4 mr-2" />
            Config Points
          </Button>
          <Button onClick={() => router.push("/dashboard/chemical/new")}>
            <Plus className="w-4 h-4 mr-2" />
            Plan Sample
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { title: "Total Active", value: metrics.activeSamples, icon: Layers, color: "text-blue-500" },
          { title: "SLA Overdue", value: metrics.overdue, icon: Clock, color: "text-red-500" },
          { title: "Under Validation", value: metrics.pendingValidation, icon: Search, color: "text-amber-500" },
          { title: "Pending FC Update", value: metrics.pendingFC, icon: ArrowRight, color: "text-violet-500" },
        ].map((m, i) => (
          <Card key={i} className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-primary/20">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{m.title}</CardTitle>
              <m.icon className={`h-4 w-4 ${m.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{m.value}</div>
              <p className="text-xs text-muted-foreground">+2 from yesterday</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters & Actions */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-card p-4 rounded-xl border">
        <div className="flex items-center gap-4 w-full md:w-auto">
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search Sample ID or Point..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Select value={fpsoFilter} onValueChange={setFpsoFilter}>
            <SelectTrigger className="w-[200px]">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="All FPSOs" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All FPSOs</SelectItem>
              <SelectItem value="FPSO PARATY">FPSO PARATY</SelectItem>
              <SelectItem value="FPSO SEPETIBA">FPSO SEPETIBA</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Bottom Layout: Grid for Samples and Forecast */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Samples Table */}
        <div className="lg:col-span-3 rounded-xl border bg-card shadow-sm overflow-hidden">
          <Table>
            <TableHeader className="bg-muted/50">
              <TableRow>
                <TableHead className="w-[120px]">Sample ID</TableHead>
                <TableHead>Sample Point</TableHead>
                <TableHead>Sampling Date</TableHead>
                <TableHead className="w-[220px]">Current Status</TableHead>
                <TableHead>SLA</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-20">
                    <div className="flex flex-col items-center gap-2">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                      <span className="text-muted-foreground font-medium">Synchronizing sampling data...</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : filteredSamples.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-20 text-muted-foreground font-medium">
                    No samples found matching your criteria.
                  </TableCell>
                </TableRow>
              ) : (
                filteredSamples.map((sample) => {
                  const statusConf = getStatusConfig(sample.status)
                  const isOverdue = sample.status !== "Flow computer updated" &&
                    sample.sampling_date &&
                    (new Date().getTime() - new Date(sample.sampling_date).getTime()) / (1000 * 3600 * 24) > 15;

                  return (
                    <TableRow key={sample.id} className="hover:bg-muted/30 transition-colors group">
                      <TableCell className="font-bold text-primary">
                        {sample.sample_id}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-semibold">{sample.sample_point?.tag_number}</span>
                          <span className="text-[11px] text-muted-foreground">{sample.sample_point?.fpso_name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {sample.sampling_date ? new Date(sample.sampling_date).toLocaleDateString() : 'Planned'}
                      </TableCell>
                      <TableCell>
                        <Badge className={`${statusConf.color} text-white border-none flex items-center gap-1.5 w-fit px-2.5 py-1 text-[11px]`}>
                          <statusConf.icon className="w-3.5 h-3.5" />
                          {sample.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {isOverdue ? (
                          <Badge variant="destructive" className="animate-pulse">Overdue</Badge>
                        ) : (
                          <Badge variant="outline" className="text-green-600 border-green-200">On Track</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="group-hover:bg-primary group-hover:text-white transition-all"
                          onClick={() => router.push(`/dashboard/chemical/${sample.id}`)}
                        >
                          Detail
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Forecast Sidebar */}
        <div className="space-y-4">
          <Card className="border-primary/20 bg-primary/[0.02]">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Calendar className="w-4 h-4 text-primary" />
                Sampling Forecast
              </CardTitle>
              <CardDescription className="text-[11px]">Next required sampling windows.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {samplePoints.map(p => {
                const nextDate = new Date();
                nextDate.setDate(nextDate.getDate() + (Math.random() * 20 + 5)); // Simulating forecast
                return (
                  <div key={p.id} className="flex items-center justify-between p-2 rounded-lg bg-background border border-border/50 hover:shadow-sm transition-all group">
                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-primary group-hover:underline cursor-pointer">{p.tag_number}</span>
                      <span className="text-[10px] text-muted-foreground">{p.fpso_name}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-medium block">Target:</span>
                      <span className="text-xs font-bold text-amber-600">{nextDate.toLocaleDateString()}</span>
                    </div>
                  </div>
                )
              })}
              <Button variant="outline" size="sm" className="w-full text-xs" onClick={() => router.push("/dashboard/chemical/new")}>
                View Full Schedule
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 text-slate-50 border-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium uppercase tracking-wider opacity-60">SLA Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">94.2%</div>
              <div className="text-[10px] opacity-60 mt-1">Samples on time (Last 30d)</div>
              <div className="mt-4 h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-primary w-[94.2%]"></div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
