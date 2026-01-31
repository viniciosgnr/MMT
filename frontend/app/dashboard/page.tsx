"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, AlertTriangle, Calendar, ClipboardList, TrendingUp, CheckCircle2, Clock } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts'

const data = [
  { name: 'Jan', calibrations: 4, compliance: 85 },
  { name: 'Feb', calibrations: 7, compliance: 88 },
  { name: 'Mar', calibrations: 5, compliance: 92 },
  { name: 'Apr', calibrations: 12, compliance: 90 },
  { name: 'May', calibrations: 8, compliance: 94 },
  { name: 'Jun', calibrations: 15, compliance: 91 },
  { name: 'Jul', calibrations: 10, compliance: 95 },
]

export default function DashboardPage() {
  return (
    <div className="space-y-8 p-2">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight text-[#003D5C]">Dashboard Overview</h1>
        <p className="text-muted-foreground">Real-time status of MMT operations and compliance.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Metric 1 - Navy Blue accent */}
        <Card className="border-l-4 border-l-[#003D5C] shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-[#003D5C]">Pending Calibrations</CardTitle>
            <Calendar className="h-4 w-4 text-[#003D5C]" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">12</div>
            <div className="flex items-center gap-1 mt-1">
              <Badge variant="secondary" className="bg-blue-50 text-[#003D5C] border-blue-100 text-[10px]">
                +2 due this week
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Metric 2 - Safety Orange accent */}
        <Card className="border-l-4 border-l-[#FF6B35] shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-[#FF6B35]">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-[#FF6B35]" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-[#FF6B35]">5</div>
            <div className="flex items-center gap-1 mt-1">
              <Badge variant="destructive" className="bg-orange-50 text-[#FF6B35] border-orange-100 hover:bg-orange-100 text-[10px]">
                3 critical
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Metric 3 - SBM Teal/Amber accent */}
        <Card className="border-l-4 border-l-amber-500 shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-amber-600">Open Failures</CardTitle>
            <ClipboardList className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">2</div>
            <div className="flex items-center gap-2 mt-1">
              <span className="flex h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
              <p className="text-xs text-muted-foreground font-medium">Waiting approval</p>
            </div>
          </CardContent>
        </Card>

        {/* Metric 4 - Cyan accent */}
        <Card className="border-l-4 border-l-cyan-600 shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-cyan-700">Upcoming Samplings</CardTitle>
            <Activity className="h-4 w-4 text-cyan-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">8</div>
            <div className="flex items-center gap-1 mt-1">
              <Badge variant="outline" className="text-cyan-700 border-cyan-200 bg-cyan-50/30 text-[10px]">
                Next 30 days
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 shadow-sm border-slate-200/60 overflow-hidden">
          <CardHeader className="border-b bg-slate-50/50 py-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg font-bold text-[#003D5C]">Calibration Execution</CardTitle>
                <p className="text-xs text-muted-foreground mt-0.5">Monthly performance and compliance trend</p>
              </div>
              <TrendingUp className="h-5 w-5 text-emerald-500" />
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorCal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#003D5C" stopOpacity={0.1} />
                      <stop offset="95%" stopColor="#003D5C" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12 }}
                    dy={10}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12 }}
                  />
                  <Tooltip
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="calibrations"
                    stroke="#003D5C"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorCal)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3 shadow-sm border-slate-200/60 overflow-hidden">
          <CardHeader className="border-b bg-slate-50/50 py-4">
            <CardTitle className="text-lg font-bold text-[#003D5C]">Recent Activity</CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">Latest updates from the platform</p>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="relative space-y-6 after:absolute after:inset-y-0 after:left-[19px] after:w-px after:bg-slate-100">
              {/* Activity Item 1 */}
              <div className="relative z-10 flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-white shadow-sm">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                </div>
                <div className="flex flex-col gap-0.5 min-w-0">
                  <p className="text-sm font-semibold text-slate-900 truncate">Certificate Issued</p>
                  <p className="text-xs text-muted-foreground font-medium">T62-PT-1103 - Pressure Transmitter</p>
                  <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                    <Clock className="h-3 w-3" />
                    2h ago
                  </div>
                </div>
              </div>

              {/* Activity Item 2 */}
              <div className="relative z-10 flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-white shadow-sm">
                  <AlertTriangle className="h-5 w-5 text-[#FF6B35]" />
                </div>
                <div className="flex flex-col gap-0.5 min-w-0">
                  <p className="text-sm font-semibold text-slate-900 truncate">Calibration Failed</p>
                  <p className="text-xs text-muted-foreground font-medium">T62-FT-1103 - Turbine Meter</p>
                  <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                    <Clock className="h-3 w-3" />
                    5h ago
                  </div>
                </div>
              </div>

              {/* Activity Item 3 - Mockup */}
              <div className="relative z-10 flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-white shadow-sm">
                  <TrendingUp className="h-5 w-5 text-blue-500" />
                </div>
                <div className="flex flex-col gap-0.5 min-w-0">
                  <p className="text-sm font-semibold text-slate-900 truncate">New Campaign Created</p>
                  <p className="text-xs text-muted-foreground font-medium">Oil Rundown Run 1 - FPSO SEPETIBA</p>
                  <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                    <Clock className="h-3 w-3" />
                    1d ago
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

