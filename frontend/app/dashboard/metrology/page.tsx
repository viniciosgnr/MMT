"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Calendar, Clock, PlayCircle, FileText, CheckCircle2, Ruler, Plus } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import { apiFetch } from "@/lib/api"

interface CalibrationTask {
  id: number
  tag: string
  description: string
  due_date: string
  status: string
  type: string
  plan_date?: string
  exec_date?: string
  campaign_id?: number
}

interface Campaign {
  id: number
  name: string
  fpso_name: string
  status: string
  responsible: string
  start_date: string
  end_date?: string
}

export default function MetrologicalConfirmationPage() {
  const [tasks, setTasks] = useState<CalibrationTask[]>([])
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaign, setSelectedCampaign] = useState<number | null>(null)
  const [selectedTask, setSelectedTask] = useState<CalibrationTask | null>(null)
  const [isInputOpen, setIsInputOpen] = useState(false)
  const [isCampaignDialogOpen, setIsCampaignDialogOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Form states
  const [readings, setReadings] = useState({ standard: "", equipment: "", uncertainty: "" })
  const [newCampaign, setNewCampaign] = useState({
    name: "",
    fpso_name: "FPSO SEPETIBA",
    responsible: "",
    start_date: "",
    end_date: ""
  })

  // Load campaigns and tasks
  useEffect(() => {
    loadData()
  }, [selectedCampaign])

  const loadData = async () => {
    try {
      setIsLoading(true)

      const [campaignsRes, tasksRes] = await Promise.all([
        apiFetch("/calibration/campaigns"),
        apiFetch(`/calibration/tasks${selectedCampaign ? `?campaign_id=${selectedCampaign}` : ''}`)
      ])

      if (campaignsRes.ok && tasksRes.ok) {
        setCampaigns(await campaignsRes.json())
        setTasks(await tasksRes.json())
      } else {
        toast.error("Failed to fetch calibration data")
      }
    } catch (error) {
      toast.error("Failed to fetch calibration data")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateCampaign = async () => {
    try {
      const res = await apiFetch("/calibration/campaigns", {
        method: "POST",
        body: JSON.stringify(newCampaign)
      })

      if (res.ok) {
        toast.success(`Campaign "${newCampaign.name}" created successfully`)
        setIsCampaignDialogOpen(false)
        setNewCampaign({
          name: "",
          fpso_name: "FPSO SEPETIBA",
          responsible: "",
          start_date: "",
          end_date: ""
        })
        loadData()
      } else {
        throw new Error("Failed")
      }
    } catch (error) {
      toast.error("Failed to create campaign")
    }
  }

  const handleSaveResults = async () => {
    if (!selectedTask) return

    try {
      const res = await apiFetch(`/calibration/tasks/${selectedTask.id}/results`, {
        method: "POST",
        body: JSON.stringify({
          standard_reading: parseFloat(readings.standard),
          equipment_reading: parseFloat(readings.equipment),
          uncertainty: readings.uncertainty ? parseFloat(readings.uncertainty) : undefined
        })
      })

      if (res.ok) {
        toast.success(`Calibration results for ${selectedTask.tag} saved successfully`)
        setIsInputOpen(false)
        setReadings({ standard: "", equipment: "", uncertainty: "" })
        loadData()
      } else {
        throw new Error("Failed")
      }
    } catch (error) {
      toast.error("Failed to save results")
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "Overdue": return "destructive"
      case "Executed": return "default"
      case "Scheduled": return "secondary"
      default: return "outline"
    }
  }

  // Create Task Dialog State
  const [isTaskDialogOpen, setIsTaskDialogOpen] = useState(false)
  const [newTask, setNewTask] = useState({
    tag: "",
    description: "",
    due_date: "",
    equipment_id: 1, // Defaulting for MVP
    campaign_id: ""
  })

  const handleCreateTask = async () => {
    try {
      const payload = {
        ...newTask,
        type: "Calibration",
        status: "Pending",
        campaign_id: newTask.campaign_id ? parseInt(newTask.campaign_id) : undefined
      }

      const res = await apiFetch("/calibration/tasks", {
        method: "POST",
        body: JSON.stringify(payload)
      })

      if (res.ok) {
        toast.success(`Task for "${newTask.tag}" created successfully`)
        setIsTaskDialogOpen(false)
        setNewTask({
          tag: "",
          description: "",
          due_date: "",
          equipment_id: 1,
          campaign_id: ""
        })
        loadData()
      } else {
        throw new Error("Failed")
      }
    } catch (error) {
      toast.error("Failed to create task")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Metrological Confirmation (M2)</h1>
          <p className="text-muted-foreground">Manage calibration campaigns, tasks and certificates.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsTaskDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> New Task
          </Button>
          <Button className="bg-[#FF6B35] hover:bg-[#e05a2b] text-white" onClick={() => setIsCampaignDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> New Campaign
          </Button>
        </div>
      </div>

      {/* Campaign Filter */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Campaign Filter</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 items-center">
            <Select
              value={selectedCampaign?.toString() || "all"}
              onValueChange={(v) => setSelectedCampaign(v === "all" ? null : parseInt(v))}
            >
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder="All campaigns" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All campaigns</SelectItem>
                {campaigns.map(c => (
                  <SelectItem key={c.id} value={c.id.toString()}>
                    {c.name} ({c.status})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Badge variant="outline">{tasks.length} tasks</Badge>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="pending" className="w-full">
        <TabsList>
          <TabsTrigger value="pending">Pending / Planned</TabsTrigger>
          <TabsTrigger value="executed">Executed / Validating</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4 mt-4">
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading tasks...</div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {tasks.filter(t => t.status !== 'Executed').map(task => (
                <Card key={task.id} className={`${task.status === 'Overdue' ? 'border-destructive/50 bg-destructive/5' : 'hover:border-[#FF6B35]/50 transition-colors'} ${task.status === 'Scheduled' ? 'border-[#003D5C]/10' : ''}`}>
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-base font-bold text-[#003D5C] hover:underline cursor-pointer" onClick={() => window.location.href = `/dashboard/calibration/tasks/${task.id}`}>{task.tag}</CardTitle>
                      <Badge variant={getStatusBadgeVariant(task.status)} className={task.status === 'Scheduled' ? 'bg-[#FF6B35] text-white' : ''}>{task.status}</Badge>
                    </div>
                    <CardDescription>{task.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="pb-2">
                    <div className="flex items-center text-sm text-muted-foreground mt-2">
                      <Calendar className="mr-2 h-4 w-4 text-[#FF6B35]" />
                      Due: <span className={task.status === 'Overdue' ? 'text-destructive font-bold ml-1' : 'ml-1'}>{task.due_date}</span>
                    </div>
                    {task.plan_date && (
                      <div className="flex items-center text-sm text-[#003D5C] mt-1 font-medium">
                        <Clock className="mr-2 h-4 w-4 text-[#FF6B35]" />
                        Planned: {task.plan_date}
                      </div>
                    )}
                  </CardContent>
                  <CardFooter className="justify-end gap-2 pt-2">
                    <Button size="sm" variant="ghost" onClick={() => window.location.href = `/dashboard/calibration/tasks/${task.id}`}>
                      View Details
                    </Button>
                    {task.status === 'Scheduled' && (
                      <Button size="sm" className="bg-[#003D5C] hover:bg-[#002d45] text-white" onClick={() => { setSelectedTask(task); setIsInputOpen(true); }}>
                        Execute
                      </Button>
                    )}
                  </CardFooter>
                </Card>
              ))}
              {tasks.filter(t => t.status !== 'Executed').length === 0 && (
                <div className="col-span-3 border rounded-lg h-64 flex items-center justify-center text-muted-foreground border-dashed">
                  No pending tasks. Create a new campaign to get started.
                </div>
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="executed" className="mt-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {tasks.filter(t => t.status === 'Executed').map(task => (
              <Card key={task.id} className="border-green-200 bg-green-50/20">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-base font-bold">{task.tag}</CardTitle>
                    <Badge className="bg-green-600 hover:bg-green-700">Executed</Badge>
                  </div>
                  <CardDescription>{task.description}</CardDescription>
                </CardHeader>
                <CardContent className="pb-2">
                  <div className="flex items-center text-sm text-muted-foreground mt-2">
                    <CheckCircle2 className="mr-2 h-4 w-4 text-green-600" />
                    Executed: {task.exec_date}
                  </div>
                </CardContent>
                <CardFooter className="justify-end gap-2 pt-2">
                  <Button size="sm" variant="outline" className="border-green-200 hover:bg-green-100 hover:text-green-800">
                    <FileText className="mr-2 h-4 w-4" /> Certificate
                  </Button>
                </CardFooter>
              </Card>
            ))}
            {tasks.filter(t => t.status === 'Executed').length === 0 && (
              <div className="col-span-3 border rounded-lg h-64 flex items-center justify-center text-muted-foreground border-dashed">
                No executed tasks yet.
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Create Campaign Dialog */}
      <Dialog open={isCampaignDialogOpen} onOpenChange={setIsCampaignDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Create New Campaign</DialogTitle>
            <DialogDescription>
              Create a new calibration campaign to organize tasks.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Campaign Name</Label>
              <Input
                placeholder="e.g., Q1 2026 Calibration"
                value={newCampaign.name}
                onChange={e => setNewCampaign({ ...newCampaign, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Responsible</Label>
              <Input
                placeholder="Engineer name"
                value={newCampaign.responsible}
                onChange={e => setNewCampaign({ ...newCampaign, responsible: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Start Date</Label>
                <Input
                  type="date"
                  value={newCampaign.start_date}
                  onChange={e => setNewCampaign({ ...newCampaign, start_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>End Date</Label>
                <Input
                  type="date"
                  value={newCampaign.end_date}
                  onChange={e => setNewCampaign({ ...newCampaign, end_date: e.target.value })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleCreateCampaign}>Create Campaign</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Task Dialog */}
      <Dialog open={isTaskDialogOpen} onOpenChange={setIsTaskDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Create New Calibration Task</DialogTitle>
            <DialogDescription>Add a new instrument to the plan.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Instrument Tag</Label>
              <Input
                placeholder="e.g. 62-FT-1201"
                value={newTask.tag}
                onChange={e => setNewTask({ ...newTask, tag: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Input
                placeholder="Oil Export Flow Trans..."
                value={newTask.description}
                onChange={e => setNewTask({ ...newTask, description: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Campaign</Label>
              <Select value={newTask.campaign_id} onValueChange={v => setNewTask({ ...newTask, campaign_id: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Campaign (Optional)" />
                </SelectTrigger>
                <SelectContent>
                  {campaigns.map(c => (
                    <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Due Date</Label>
              <Input
                type="date"
                value={newTask.due_date}
                onChange={e => setNewTask({ ...newTask, due_date: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleCreateTask}>Create Task</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Input Results Dialog */}
      <Dialog open={isInputOpen} onOpenChange={setIsInputOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Input Calibration Results</DialogTitle>
            <DialogDescription>
              Enter the readings for {selectedTask?.tag}.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Standard Reading</Label>
                <div className="relative">
                  <Ruler className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input className="pl-8" placeholder="e.g. 10.00" value={readings.standard} onChange={e => setReadings({ ...readings, standard: e.target.value })} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Equipment Reading</Label>
                <div className="relative">
                  <Clock className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input className="pl-8" placeholder="e.g. 10.05" value={readings.equipment} onChange={e => setReadings({ ...readings, equipment: e.target.value })} />
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Uncertainty (optional)</Label>
              <Input placeholder="e.g. 0.01" value={readings.uncertainty} onChange={e => setReadings({ ...readings, uncertainty: e.target.value })} />
            </div>
            <div className="p-3 bg-muted/30 rounded text-sm text-muted-foreground">
              Deviation: {readings.standard && readings.equipment ? (Math.abs(Number(readings.standard) - Number(readings.equipment))).toFixed(3) : '-'}
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleSaveResults}>Save & Complete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
