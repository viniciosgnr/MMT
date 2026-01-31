"use client"

import { useState, useEffect, useMemo } from "react"
import {
  Calendar as CalIcon,
  List as ListIcon,
  Download,
  ChevronLeft,
  ChevronRight,
  Filter,
  ArrowUpRight,
  MoreVertical,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ClipboardList
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths, startOfWeek, endOfWeek } from "date-fns"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { ACTIVITY_TYPES, TYPE_COLORS, TrafficLight } from "./planning-utils"
import { ActivityActionDialog } from "./task-dialogs"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export default function PlanningPage() {
  const [view, setView] = useState("calendar")
  const [currentDate, setCurrentDate] = useState(new Date())
  const [fpsos] = useState(["FPSO SEPETIBA", "FPSO SAQUAREMA", "FPSO MARICÁ", "FPSO PARATY", "FPSO ILHABELA"])
  const [filters, setFilters] = useState({
    fpso: "All FPSOs",
    type: "All Activities"
  })

  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedActivity, setSelectedActivity] = useState<any>(null)
  const [dialogMode, setDialogMode] = useState<'complete' | 'mitigate'>('complete')
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const fetchActivities = async () => {
    setLoading(true)
    try {
      const start = startOfMonth(currentDate)
      const end = endOfMonth(currentDate)
      let url = `${API_URL}/planning/activities?start_date=${format(start, 'yyyy-MM-dd')}&end_date=${format(end, 'yyyy-MM-dd')}`

      if (filters.fpso !== "All FPSOs") url += `&fpso_name=${filters.fpso}`
      if (filters.type !== "All Activities") url += `&activity_type=${filters.type}`

      const res = await fetch(url)
      const data = await res.json()
      setActivities(Array.isArray(data) ? data : [])
    } catch (e) {
      toast.error("Failed to load activities")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchActivities()
  }, [currentDate, filters])

  // Calendar Logic
  const monthStart = startOfMonth(currentDate)
  const monthEnd = endOfMonth(currentDate)
  const calendarStart = startOfWeek(monthStart)
  const calendarEnd = endOfWeek(monthEnd)
  const calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  const activitiesByDay = useMemo(() => {
    const map: Record<string, any[]> = {}
    activities.forEach(act => {
      const dayKey = format(new Date(act.scheduled_date), 'yyyy-MM-dd')
      if (!map[dayKey]) map[dayKey] = []
      map[dayKey].push(act)
    })
    return map
  }, [activities])

  const handleTaskClick = (act: any, mode: 'complete' | 'mitigate') => {
    setSelectedActivity(act)
    setDialogMode(mode)
    setIsDialogOpen(true)
  }

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tighter text-[#003D5C] uppercase italic">
            Planning <span className="text-[#FF6B35]">(M8)</span>
          </h1>
          <p className="text-slate-500 text-sm font-medium">Coordinate, schedule, and report all critical metering activities.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="border-[#003D5C]/20 text-[#003D5C] hover:bg-[#003D5C]/5">
            <Download className="mr-2 h-4 w-4" /> Export Actions
          </Button>
          <Button className="bg-[#FF6B35] hover:bg-[#e05a2b] text-white shadow-lg shadow-orange-500/20 font-bold uppercase text-xs tracking-widest px-6">
            New Strategy
          </Button>
        </div>
      </div>

      {/* Control Bar */}
      <Card className="border-[#003D5C]/10 shadow-xl shadow-slate-200/50 bg-white/80 backdrop-blur-md sticky top-0 z-10">
        <CardContent className="p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg">
              <Button
                variant={view === "calendar" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setView("calendar")}
                className={view === "calendar" ? "bg-white shadow-sm font-bold text-[#003D5C]" : "text-slate-500 font-medium"}
              >
                <CalIcon className="mr-2 h-4 w-4" /> Calendar
              </Button>
              <Button
                variant={view === "list" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setView("list")}
                className={view === "list" ? "bg-white shadow-sm font-bold text-[#003D5C]" : "text-slate-500 font-medium"}
              >
                <ListIcon className="mr-2 h-4 w-4" /> List View
              </Button>
            </div>

            <div className="h-8 w-[1px] bg-slate-200 mx-2 hidden md:block" />

            <div className="flex items-center gap-2">
              <Select value={filters.fpso} onValueChange={(v) => setFilters({ ...filters, fpso: v })}>
                <SelectTrigger className="w-[180px] h-9 text-xs font-bold border-none shadow-none bg-slate-50">
                  <SelectValue placeholder="Select FPSO" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All FPSOs">All FPSOs</SelectItem>
                  {fpsos.map(f => <SelectItem key={f} value={f}>{f}</SelectItem>)}
                </SelectContent>
              </Select>

              <Select value={filters.type} onValueChange={(v) => setFilters({ ...filters, type: v })}>
                <SelectTrigger className="w-[200px] h-9 text-xs font-bold border-none shadow-none bg-slate-50">
                  <SelectValue placeholder="Activity Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All Activities">All Activities</SelectItem>
                  {ACTIVITY_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center bg-slate-100 rounded-lg p-1">
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setCurrentDate(subMonths(currentDate, 1))}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <div className="px-4 text-xs font-black text-[#003D5C] uppercase tracking-widest min-w-[140px] text-center">
                {format(currentDate, "MMMM yyyy")}
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setCurrentDate(addMonths(currentDate, 1))}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            <Button variant="outline" size="sm" onClick={() => setCurrentDate(new Date())} className="font-bold text-[10px] uppercase">Today</Button>
          </div>
        </CardContent>
      </Card>

      {view === "calendar" ? (
        <div className="grid grid-cols-7 gap-px bg-slate-200 rounded-2xl overflow-hidden border border-slate-200 shadow-2xl">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
            <div key={d} className="bg-slate-50 p-4 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest">
              {d}
            </div>
          ))}
          {calendarDays.map((day, idx) => {
            const dayKey = format(day, 'yyyy-MM-dd')
            const dayActivities = activitiesByDay[dayKey] || []
            const isToday = isSameDay(day, new Date())
            const currentMonth = isSameMonth(day, currentDate)

            return (
              <div
                key={dayKey}
                className={cn(
                  "min-h-[140px] bg-white p-2 flex flex-col gap-1 transition-all group hover:bg-slate-50/50",
                  !currentMonth && "bg-slate-50/30 text-slate-300",
                  isToday && "relative after:absolute after:top-0 after:left-0 after:right-0 after:h-1 after:bg-[#FF6B35]"
                )}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className={cn(
                    "text-xs font-black",
                    isToday ? "text-[#FF6B35]" : "text-[#003D5C]/40"
                  )}>
                    {format(day, 'd')}
                  </span>
                  {dayActivities.length > 0 && (
                    <Badge variant="outline" className="text-[9px] h-4 px-1 border-slate-200 text-slate-400 bg-white">
                      {dayActivities.length}
                    </Badge>
                  )}
                </div>

                <div className="flex-1 space-y-1 overflow-y-auto max-h-[120px] scrollbar-hide">
                  {dayActivities.map(act => (
                    <Popover key={act.id}>
                      <PopoverTrigger asChild>
                        <div
                          className={cn(
                            "p-1.5 rounded-md text-[10px] font-bold border truncate cursor-pointer transition-transform hover:scale-[1.02] active:scale-95 flex items-center gap-1.5 shadow-sm",
                            TYPE_COLORS[act.type] || "bg-slate-100"
                          )}
                        >
                          <TrafficLight status={act.status} scheduledDate={act.scheduled_date} />
                          <span className="truncate">{act.title}</span>
                        </div>
                      </PopoverTrigger>
                      <PopoverContent className="w-64 p-3 shadow-2xl rounded-xl border-[#003D5C]/10">
                        <div className="space-y-3">
                          <div className="flex justify-between items-start">
                            <Badge className={TYPE_COLORS[act.type] + " border-none text-[9px]"}>
                              {act.type}
                            </Badge>
                            <div className="flex gap-1">
                              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleTaskClick(act, 'complete')}><CheckCircle2 className="h-4 w-4 text-green-500" /></Button>
                              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleTaskClick(act, 'mitigate')}><AlertTriangle className="h-4 w-4 text-amber-500" /></Button>
                            </div>
                          </div>
                          <div>
                            <h4 className="text-sm font-black text-[#003D5C] leading-tight mb-1">{act.title}</h4>
                            <p className="text-[10px] text-slate-500 leading-relaxed line-clamp-2">{act.description}</p>
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-slate-400 font-bold uppercase tracking-tighter pt-2 border-t">
                            <Clock className="h-3 w-3" /> Due {format(new Date(act.scheduled_date), 'HH:mm')}
                          </div>
                        </div>
                      </PopoverContent>
                    </Popover>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(activitiesByDay).sort().reverse().map(([dateKey, dayActs]) => (
            <div key={dateKey} className="space-y-2">
              <div className="flex items-center gap-3 py-2">
                <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.2em]">
                  {format(new Date(dateKey), 'EEEE, MMMM do')}
                </h3>
                <div className="h-[1px] flex-1 bg-slate-100" />
              </div>
              <div className="grid gap-2">
                {dayActs.map(act => (
                  <Card key={act.id} className="border-[#003D5C]/5 hover:border-[#FF6B35]/30 transition-all group">
                    <CardContent className="p-3 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 flex-1">
                        <div className="h-10 w-10 rounded-full bg-slate-50 flex items-center justify-center shrink-0">
                          <TrafficLight status={act.status} scheduledDate={act.scheduled_date} />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <Badge variant="outline" className={cn("text-[9px] uppercase border-none px-0 font-black", TYPE_COLORS[act.type]?.split(' ')[1])}>
                              {act.type}
                            </Badge>
                            <span className="text-[10px] text-slate-400">•</span>
                            <span className="text-[10px] text-slate-400 font-bold uppercase">{act.fpso_name}</span>
                          </div>
                          <h4 className="text-sm font-bold text-[#003D5C] truncate">{act.title}</h4>
                        </div>
                      </div>

                      <div className="flex items-center gap-10">
                        <div className="hidden lg:block text-right">
                          <div className="text-[10px] font-black text-slate-400 uppercase mb-1">Responsible</div>
                          <div className="text-xs font-bold text-[#003D5C]">{act.responsible}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm" onClick={() => handleTaskClick(act, 'complete')} className="text-green-600 hover:text-green-700 hover:bg-green-50 font-bold text-xs">Complete</Button>
                          <Button variant="ghost" size="sm" onClick={() => handleTaskClick(act, 'mitigate')} className="text-amber-600 hover:text-amber-700 hover:bg-amber-50 font-bold text-xs">Mitigate</Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8"><MoreVertical className="h-4 w-4 text-slate-400" /></Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}

          {activities.length === 0 && !loading && (
            <div className="py-20 text-center space-y-4">
              <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto">
                <ClipboardList className="h-8 w-8 text-slate-300" />
              </div>
              <div>
                <p className="text-sm font-black text-[#003D5C] uppercase tracking-widest">No activities detected</p>
                <p className="text-xs text-slate-400">Try adjusting your filters or time period.</p>
              </div>
            </div>
          )}
        </div>
      )}

      {selectedActivity && (
        <ActivityActionDialog
          activity={selectedActivity}
          mode={dialogMode}
          open={isDialogOpen}
          onOpenChange={setIsDialogOpen}
          onRefresh={fetchActivities}
        />
      )}
    </div>
  )
}
