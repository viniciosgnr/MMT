"use client"
import Link from "next/link"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Activity, AlertOctagon, CalendarSearch, FileWarning, Target, ArrowRightCircle, ShieldAlert, Clock } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const complianceData = [
  { month: 'Oct', onTime: 45, overdue: 5 },
  { month: 'Nov', onTime: 52, overdue: 3 },
  { month: 'Dec', onTime: 48, overdue: 6 },
  { month: 'Jan', onTime: 61, overdue: 2 },
  { month: 'Feb', onTime: 55, overdue: 4 },
  { month: 'Mar', onTime: 38, overdue: 1 },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col gap-1.5">
        <h1 className="text-3xl font-bold tracking-tight text-[#003D5C]">Fleet Compliance Overview</h1>
        <p className="text-muted-foreground text-sm font-medium">Real-time SLA adherence, actionable alerts, and operational metrology status.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Metric 1 - Active Metering Tags (M1/M11) */}
        <Link href="/dashboard/configurations">
          <Card className="border-l-4 border-l-[#003D5C] shadow-sm relative overflow-hidden hover:shadow-md transition-shadow cursor-pointer h-full">
            <div className="absolute right-0 top-0 opacity-5 pt-2 pr-2">
              <Activity className="h-20 w-20" />
            </div>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-bold text-slate-700 group-hover:text-[#003D5C]">Active Metering Tags</CardTitle>
              <Activity className="h-4 w-4 text-[#003D5C]" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-[#003D5C]">1,452</div>
              <div className="flex items-center gap-1 mt-1.5">
                <Badge variant="secondary" className="bg-slate-50 text-slate-600 text-[10px] font-bold tracking-wide border-slate-200">
                  ACTIVE TAGS ACROSS 10 FPSOS
                </Badge>
              </div>
            </CardContent>
          </Card>
        </Link>

        {/* Metric 2 - SLA Target Health */}
        <Link href="/dashboard/monitoring">
          <Card className="border-l-4 border-l-emerald-600 shadow-sm relative overflow-hidden hover:shadow-md transition-shadow cursor-pointer h-full">
            <div className="absolute right-0 top-0 opacity-10 pt-2 pr-2">
              <Target className="h-20 w-20" />
            </div>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-bold text-slate-700">SLA Compliance Rate</CardTitle>
              <ShieldAlert className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-[#003D5C]">94.2%</div>
              <div className="flex items-center gap-1 mt-1.5">
                <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px] font-bold tracking-wide">
                  +1.2% VS LAST MONTH
                </Badge>
              </div>
            </CardContent>
          </Card>
        </Link>

        {/* Metric 3 - Scheduled Activities */}
        <Link href="/dashboard/planning">
          <Card className="border-l-4 border-l-blue-500 shadow-sm relative overflow-hidden hover:shadow-md transition-shadow cursor-pointer h-full">
            <div className="absolute right-0 top-0 opacity-5 pt-2 pr-2">
              <CalendarSearch className="h-20 w-20" />
            </div>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-bold text-slate-700">Scheduled Calibrations & Samples</CardTitle>
              <CalendarSearch className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-[#003D5C]">45</div>
              <div className="flex items-center gap-1 mt-1.5">
                <Badge variant="secondary" className="bg-blue-50 text-blue-700 text-[10px] font-bold tracking-wide border-blue-200">
                  SCHEDULED FOR THIS MONTH
                </Badge>
              </div>
            </CardContent>
          </Card>
        </Link>

        {/* Metric 4 - Active Regulatory Risks */}
        <Link href="/dashboard/failure-notification">
          <Card className="border-l-4 border-l-amber-500 shadow-sm relative overflow-hidden hover:shadow-md transition-shadow cursor-pointer h-full">
            <div className="absolute right-0 top-0 opacity-10 pt-2 pr-2">
              <AlertOctagon className="h-20 w-20" />
            </div>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-bold text-slate-700">Critical Alerts & Failures</CardTitle>
              <AlertOctagon className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold text-[#003D5C]">5</div>
              <div className="flex items-center gap-1 mt-1.5">
                <Badge variant="destructive" className="bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100 text-[10px] font-bold tracking-wide">
                  COMBINED CRITICAL ALERTS
                </Badge>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">

        {/* Main Analytics Chart */}
        <Card className="col-span-4 shadow-sm border-slate-200">
          <CardHeader className="border-b bg-slate-50/80 py-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold text-[#003D5C]">Workflow Execution & SLA Adherence (M2/M3)</CardTitle>
                <CardDescription className="text-xs font-medium mt-1">Monthly breakdown of On-Time vs Overdue flow computer updates.</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-4 pb-2">
            <div className="h-[240px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={complianceData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis
                    dataKey="month"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }}
                    dy={10}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }}
                  />
                  <Tooltip
                    cursor={{ fill: '#f8fafc' }}
                    contentStyle={{ borderRadius: '6px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    itemStyle={{ fontWeight: 600 }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', fontWeight: 500, paddingTop: '10px' }} />
                  <Bar dataKey="onTime" name="Executed On-Time" stackId="a" fill="#003D5C" radius={[0, 0, 4, 4]} barSize={32} />
                  <Bar dataKey="overdue" name="SLA Breached" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Priority Action Center */}
        <Card className="col-span-3 shadow-sm border-slate-200">
          <CardHeader className="border-b bg-rose-50/50 py-4">
            <CardTitle className="text-base font-bold text-red-900">Priority Action Center</CardTitle>
            <CardDescription className="text-xs font-medium mt-1 text-red-700/80">Items requiring immediate engineering intervention.</CardDescription>
          </CardHeader>
          <CardContent className="pt-4 overflow-y-auto max-h-[260px]">
            <div className="space-y-4">

              {/* Action Item 1 */}
              <div className="group relative flex flex-col gap-2 rounded-lg border border-red-100 bg-white p-3 hover:border-red-300 transition-colors shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertOctagon className="h-4 w-4 text-red-600" />
                    <span className="text-xs font-bold text-red-600 uppercase tracking-wider">Critical Analysis Reproved</span>
                  </div>
                  <Badge variant="outline" className="text-[9px] h-5 bg-slate-50 border-slate-200 text-slate-500">
                    2H AGO
                  </Badge>
                </div>
                <div className="flex flex-col">
                  <p className="text-sm font-bold text-slate-900">Gas Chromatography (CRO) - FPSO Cidade de Ilhabela</p>
                  <p className="text-xs text-slate-600 mt-0.5"><span className="font-semibold">T73-FT-5801</span> • C1 Methane fraction deviation exceeds 2-sigma historical limit line.</p>
                </div>
                <div className="flex items-center justify-start mt-2">
                  <button className="text-xs font-bold text-[#003D5C] hover:text-blue-700 flex items-center gap-1 bg-blue-50 px-2 py-1 rounded">
                    Schedule Emergency Sample <ArrowRightCircle className="h-3 w-3" />
                  </button>
                </div>
              </div>

              {/* Action Item 2 */}
              <div className="group relative flex flex-col gap-2 rounded-lg border border-amber-100 bg-white p-3 hover:border-amber-300 transition-colors shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-amber-600" />
                    <span className="text-xs font-bold text-amber-600 uppercase tracking-wider">SLA Breach Warning</span>
                  </div>
                  <Badge variant="outline" className="text-[9px] h-5 bg-slate-50 border-slate-200 text-slate-500">
                    DAY 14 OF 15
                  </Badge>
                </div>
                <div className="flex flex-col">
                  <p className="text-sm font-bold text-slate-900">Pending FC Update (Custody Transfer)</p>
                  <p className="text-xs text-slate-600 mt-0.5"><span className="font-semibold">T62-PT-1103</span> • Calibration certified, pending Flow Computer deployment before SLA C+15 expires.</p>
                </div>
              </div>

              {/* Action Item 3 */}
              <div className="group relative flex flex-col gap-2 rounded-lg border border-amber-100 bg-white p-3 hover:border-amber-300 transition-colors shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileWarning className="h-4 w-4 text-amber-600" />
                    <span className="text-xs font-bold text-amber-600 uppercase tracking-wider">NFSM Approaching Limit</span>
                  </div>
                  <Badge variant="outline" className="text-[9px] h-5 bg-slate-50 border-slate-200 text-slate-500">
                    205H OPEN
                  </Badge>
                </div>
                <div className="flex flex-col">
                  <p className="text-sm font-bold text-slate-900">Failure Notification - Initial Report</p>
                  <p className="text-xs text-slate-600 mt-0.5"><span className="font-semibold">FPSO Sepetiba</span> • Flare Meter fault detected. Initial NFSM xml submission required before 240h ANP deadline.</p>
                </div>
              </div>

            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

