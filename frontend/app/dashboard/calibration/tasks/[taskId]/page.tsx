"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { toast } from "sonner"
import { Calendar, CheckCircle2, Clock, FileCheck, Seal, Upload, AlertCircle } from "lucide-react"
import { planCalibration, executeCalibration, uploadCertificate, validateCertificate, getTagSealHistory } from "@/lib/api"

export default function CalibrationTaskDetail() {
  const params = useParams()
  const router = useRouter()
  const taskId = parseInt(params.taskId as string)

  const [task, setTask] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [sealHistory, setSealHistory] = useState<any[]>([])

  // Plan dialog state
  const [planDialogOpen, setPlanDialogOpen] = useState(false)
  const [planNotes, setPlanNotes] = useState("")

  // Execute dialog state
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false)
  const [execData, setExecData] = useState({
    execution_date: new Date().toISOString().split('T')[0],
    completion_date: new Date().toISOString().split('T')[0],
    calibration_type: "in-situ",
    seal_number: "",
    seal_date: new Date().toISOString().split('T')[0],
    seal_location: "Terminal Block",
    seal_type: "Wire"
  })

  // Certificate dialog state
  const [certDialogOpen, setCertDialogOpen] = useState(false)
  const [certData, setCertData] = useState({
    certificate_number: "",
    issue_date: new Date().toISOString().split('T')[0],
    uncertainty: "",
    standard_reading: "",
    equipment_reading: ""
  })

  // Issue Certificate Dialog
  const [issueDialogOpen, setIssueDialogOpen] = useState(false)
  const [issueData, setIssueData] = useState({
    template: "Standard Calibration Certificate (ISO 5167)",
    signatory: "Metrologist A",
    notes: ""
  })

  useEffect(() => {
    fetchTaskDetails()
  }, [taskId])

  async function fetchTaskDetails() {
    try {
      setLoading(true)
      const res = await fetch(`http://localhost:8000/api/calibration/tasks/${taskId}`)
      const data = await res.json()
      setTask(data)

      // Fetch seal history if task has equipment with tag
      if (data.equipment_id) {
        // For now, we'll skip this as we need tag_id
      }
    } catch (error) {
      console.error("Error fetching task:", error)
      toast.error("Failed to load task details")
    } finally {
      setLoading(false)
    }
  }

  async function handlePlan() {
    try {
      await planCalibration(taskId, { notes: planNotes })
      toast.success("Calibration planned successfully")
      setPlanDialogOpen(false)
      fetchTaskDetails()
    } catch (error) {
      console.error("Error planning calibration:", error)
      toast.error("Failed to plan calibration")
    }
  }

  async function handleExecute() {
    try {
      await executeCalibration(taskId, execData)
      toast.success("Calibration executed successfully")
      setExecuteDialogOpen(false)
      fetchTaskDetails()
    } catch (error) {
      console.error("Error executing calibration:", error)
      toast.error("Failed to execute calibration")
    }
  }

  async function handleUploadCertificate() {
    try {
      const payload = {
        certificate_number: certData.certificate_number,
        issue_date: certData.issue_date,
        uncertainty: certData.uncertainty ? parseFloat(certData.uncertainty) : undefined,
        standard_reading: certData.standard_reading ? parseFloat(certData.standard_reading) : undefined,
        equipment_reading: certData.equipment_reading ? parseFloat(certData.equipment_reading) : undefined,
      }
      await uploadCertificate(taskId, payload)
      toast.success("Certificate uploaded successfully")
      setCertDialogOpen(false)
      fetchTaskDetails()
    } catch (error) {
      console.error("Error uploading certificate:", error)
      toast.error("Failed to upload certificate")
    }
  }

  async function handleIssueCertificate() {
    try {
      // Simulate generation by "uploading" a generated record
      const payload = {
        certificate_number: `CERT-${new Date().getFullYear()}-${Math.floor(Math.random() * 10000)}`,
        issue_date: new Date().toISOString().split('T')[0],
        uncertainty: 0.15, // Mock calculated value
        standard_reading: 100.00,
        equipment_reading: 100.05,
      }
      await uploadCertificate(taskId, payload)
      toast.success("Certificate generated and signed successfully")
      setIssueDialogOpen(false)
      fetchTaskDetails()
    } catch (error) {
      console.error("Error issuing certificate:", error)
      toast.error("Failed to issue certificate")
    }
  }

  async function handleValidateCertificate() {
    try {
      const result = await validateCertificate(taskId)
      if (result.issues && result.issues.length > 0) {
        toast.warning(`Validation completed with ${result.issues.length} issue(s)`)
      } else {
        toast.success("Certificate validated successfully")
      }
      fetchTaskDetails()
    } catch (error) {
      console.error("Error validating certificate:", error)
      toast.error("Failed to validate certificate")
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  if (!task) {
    return <div className="p-8">Task not found</div>
  }

  const statusColor = {
    "Pending": "bg-gray-500",
    "Planned": "bg-blue-500",
    "Executed": "bg-yellow-500",
    "Completed": "bg-green-500"
  }[task.status] || "bg-gray-500"

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{task.tag}</h1>
          <p className="text-muted-foreground">{task.description}</p>
        </div>
        <Badge className={statusColor}>{task.status}</Badge>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Task Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Type:</span>
              <span className="font-medium">{task.type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Due Date:</span>
              <span className="font-medium">{task.due_date}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Calibration Type:</span>
              <span className="font-medium">{task.calibration_type || "Not set"}</span>
            </div>
            {task.plan_date && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Planned Date:</span>
                <span className="font-medium">{task.plan_date}</span>
              </div>
            )}
            {task.exec_date && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Execution Date:</span>
                <span className="font-medium">{task.exec_date}</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Seal Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {task.seal_number ? (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Seal Number:</span>
                  <span className="font-medium">{task.seal_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Location:</span>
                  <span className="font-medium">{task.seal_location}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Installation Date:</span>
                  <span className="font-medium">{task.seal_installation_date}</span>
                </div>
              </>
            ) : (
              <p className="text-muted-foreground">No seal installed yet</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Certificate Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {task.certificate_number ? (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Certificate Number:</span>
                  <span className="font-medium">{task.certificate_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Issue Date:</span>
                  <span className="font-medium">{task.certificate_issued_date}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">CA Status:</span>
                  <Badge variant={task.certificate_ca_status === "approved" ? "default" : "secondary"}>
                    {task.certificate_ca_status || "pending"}
                  </Badge>
                </div>
                {task.is_temporary === 1 && (
                  <div className="flex items-center gap-2 text-yellow-600">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm">Temporary completion - awaiting definitive certificate</span>
                  </div>
                )}
              </>
            ) : (
              <p className="text-muted-foreground">No certificate uploaded yet</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Workflow Actions</CardTitle>
            <CardDescription>Transition the task through calibration workflow</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {task.status === "Pending" && (
              <Dialog open={planDialogOpen} onOpenChange={setPlanDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="w-full" variant="outline">
                    <Calendar className="mr-2 h-4 w-4" />
                    Plan Calibration
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Plan Calibration</DialogTitle>
                    <DialogDescription>Schedule this calibration task</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="plan-notes">Notes</Label>
                      <Textarea
                        id="plan-notes"
                        value={planNotes}
                        onChange={(e) => setPlanNotes(e.target.value)}
                        placeholder="Add planning notes..."
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button onClick={handlePlan}>Confirm Plan</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}

            {task.status === "Planned" && (
              <Dialog open={executeDialogOpen} onOpenChange={setExecuteDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="w-full" variant="outline">
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Execute Calibration
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Execute Calibration</DialogTitle>
                    <DialogDescription>Record calibration execution details</DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="exec-date">Execution Date</Label>
                        <Input
                          id="exec-date"
                          type="date"
                          value={execData.execution_date}
                          onChange={(e) => setExecData({ ...execData, execution_date: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="completion-date">Completion Date</Label>
                        <Input
                          id="completion-date"
                          type="date"
                          value={execData.completion_date}
                          onChange={(e) => setExecData({ ...execData, completion_date: e.target.value })}
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="cal-type">Calibration Type</Label>
                      <Select value={execData.calibration_type} onValueChange={(v) => setExecData({ ...execData, calibration_type: v })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="in-situ">In-Situ</SelectItem>
                          <SelectItem value="ex-situ">Ex-Situ</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="seal-number">Seal Number</Label>
                        <Input
                          id="seal-number"
                          value={execData.seal_number}
                          onChange={(e) => setExecData({ ...execData, seal_number: e.target.value })}
                          placeholder="e.g., SEAL-2024-001"
                        />
                      </div>
                      <div>
                        <Label htmlFor="seal-date">Seal Installation Date</Label>
                        <Input
                          id="seal-date"
                          type="date"
                          value={execData.seal_date}
                          onChange={(e) => setExecData({ ...execData, seal_date: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="seal-location">Seal Location</Label>
                        <Select value={execData.seal_location} onValueChange={(v) => setExecData({ ...execData, seal_location: v })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Terminal Block">Terminal Block</SelectItem>
                            <SelectItem value="Transmitter Body">Transmitter Body</SelectItem>
                            <SelectItem value="Junction Box">Junction Box</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="seal-type">Seal Type</Label>
                        <Select value={execData.seal_type} onValueChange={(v) => setExecData({ ...execData, seal_type: v })}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Wire">Wire</SelectItem>
                            <SelectItem value="Plastic">Plastic</SelectItem>
                            <SelectItem value="Lead">Lead</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button onClick={handleExecute}>Confirm Execution</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}



            {task.status === "Executed" && (
              <div className="space-y-2">
                <Dialog open={certDialogOpen} onOpenChange={setCertDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="w-full" variant="outline">
                      <Upload className="mr-2 h-4 w-4" />
                      Upload External Certificate
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Upload Certificate</DialogTitle>
                      <DialogDescription>Enter certificate details</DialogDescription>
                    </DialogHeader>
                    {/* ... existing upload fields ... */}
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="cert-number">Certificate Number</Label>
                        <Input
                          id="cert-number"
                          value={certData.certificate_number}
                          onChange={(e) => setCertData({ ...certData, certificate_number: e.target.value })}
                          placeholder="e.g., CERT-2024-001"
                        />
                      </div>
                      <div>
                        <Label htmlFor="cert-date">Issue Date</Label>
                        <Input
                          id="cert-date"
                          type="date"
                          value={certData.issue_date}
                          onChange={(e) => setCertData({ ...certData, issue_date: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="uncertainty">Uncertainty (%)</Label>
                        <Input
                          id="uncertainty"
                          type="number"
                          step="0.01"
                          value={certData.uncertainty}
                          onChange={(e) => setCertData({ ...certData, uncertainty: e.target.value })}
                          placeholder="e.g., 0.5"
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button onClick={handleUploadCertificate}>Upload Certificate</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>

                <Dialog open={issueDialogOpen} onOpenChange={setIssueDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="w-full bg-[#003D5C] hover:bg-[#FF6B35] text-white">
                      <Seal className="mr-2 h-4 w-4" />
                      Issue Internal Certificate (Auto-Gen)
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Issue Certificate</DialogTitle>
                      <DialogDescription>Generate and sign MMT-compliant certificate (Spec 6.4)</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="bg-slate-50 p-4 rounded border">
                        <h4 className="font-bold text-sm mb-2">Generation Preview</h4>
                        <p className="text-xs text-slate-500">Based on execution data from {task.exec_date}</p>
                        <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                          <div><strong>Uncertainty calc:</strong> 0.15%</div>
                          <div><strong>Template:</strong> ISO 5167</div>
                        </div>
                      </div>
                      <div>
                        <Label>Signatory</Label>
                        <Input value={issueData.signatory} onChange={(e) => setIssueData({ ...issueData, signatory: e.target.value })} />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button onClick={handleIssueCertificate} className="bg-emerald-600">
                        Sign & Issue
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            )}

            {task.certificate_number && task.certificate_ca_status !== "approved" && (
              <Button className="w-full" variant="outline" onClick={handleValidateCertificate}>
                <FileCheck className="mr-2 h-4 w-4" />
                Validate Certificate
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
