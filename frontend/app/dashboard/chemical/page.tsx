"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
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
import { Search, FlaskConical, FileCheck, Layers, User, Plus } from "lucide-react"
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
import {
  fetchSamplingCampaigns,
  fetchSamples,
  createSamplingCampaign,
  createSample,
  updateSampleStatus
} from "@/lib/api"
import { toast } from "sonner"

interface Sample {
  id: number
  sample_id: string
  type: string
  collection_date: string
  location: string
  status: string
  responsible: string
  campaign_id: number
  compliance_status?: string
  lab_report_url?: string
}

interface Campaign {
  id: number
  name: string
  fpso_name: string
  status: string
  responsible: string
}

export default function ChemicalAnalysisPage() {
  const [samples, setSamples] = useState<Sample[]>([])
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaign, setSelectedCampaign] = useState<number | null>(null)
  const [isCampaignDialogOpen, setIsCampaignDialogOpen] = useState(false)
  const [isSampleDialogOpen, setIsSampleDialogOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const [newCampaign, setNewCampaign] = useState({
    name: "",
    fpso_name: "FPSO SEPETIBA",
    responsible: "",
    start_date: "",
    end_date: ""
  })

  const [newSample, setNewSample] = useState({
    sample_id: "",
    type: "Oil",
    collection_date: "",
    location: "",
    responsible: "",
    campaign_id: 0
  })

  useEffect(() => {
    loadData()
  }, [selectedCampaign])

  const loadData = async () => {
    try {
      setIsLoading(true)
      const [campaignsData, samplesData] = await Promise.all([
        fetchSamplingCampaigns(),
        fetchSamples(selectedCampaign || undefined)
      ])
      setCampaigns(campaignsData)
      setSamples(samplesData)
    } catch (error) {
      toast.error("Failed to fetch chemical analysis data")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateCampaign = async () => {
    try {
      await createSamplingCampaign(newCampaign)
      toast.success(`Sampling campaign "${newCampaign.name}" created successfully`)
      setIsCampaignDialogOpen(false)
      setNewCampaign({
        name: "",
        fpso_name: "FPSO SEPETIBA",
        responsible: "",
        start_date: "",
        end_date: ""
      })
      loadData()
    } catch (error) {
      toast.error("Failed to create campaign")
    }
  }

  const handleCreateSample = async () => {
    try {
      await createSample(newSample)
      toast.success(`Sample ${newSample.sample_id} registered successfully`)
      setIsSampleDialogOpen(false)
      setNewSample({
        sample_id: "",
        type: "Oil",
        collection_date: "",
        location: "",
        responsible: "",
        campaign_id: 0
      })
      loadData()
    } catch (error) {
      toast.error("Failed to register sample")
    }
  }

  const getCampaignName = (campaignId: number) => {
    const campaign = campaigns.find(c => c.id === campaignId)
    return campaign?.name || "Unknown"
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "Collected": return "outline"
      case "In Lab": return "secondary"
      case "Analyzed": return "default"
      case "Approved": return "default"
      default: return "outline"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Chemical Analysis (M3)</h1>
          <p className="text-muted-foreground">Manage oil and gas sampling campaigns and laboratory reports.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsCampaignDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> New Campaign
          </Button>
          <Button onClick={() => setIsSampleDialogOpen(true)}>
            <FlaskConical className="mr-2 h-4 w-4" /> Register Sample
          </Button>
        </div>
      </div>

      {/* Campaign Filter */}
      <div className="flex items-center gap-2">
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
        <Badge variant="outline">{samples.length} samples</Badge>
      </div>

      <div className="rounded-md border bg-card">
        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">Loading samples...</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sample ID</TableHead>
                <TableHead>Point & Campaign</TableHead>
                <TableHead>Date / Responsible</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Compliance</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {samples.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    No samples found. Create a campaign and register samples to get started.
                  </TableCell>
                </TableRow>
              ) : (
                samples.map((spl) => (
                  <TableRow key={spl.id}>
                    <TableCell className="font-medium">{spl.sample_id}</TableCell>
                    <TableCell>
                      <div className="font-medium">{spl.location}</div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Layers className="h-3 w-3" /> {getCampaignName(spl.campaign_id)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>{spl.collection_date}</div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <User className="h-3 w-3" /> {spl.responsible}
                      </div>
                    </TableCell>
                    <TableCell>{spl.type}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(spl.status)}>{spl.status}</Badge>
                    </TableCell>
                    <TableCell>
                      {spl.compliance_status === 'Compliant' && <Badge className="bg-green-600">Compliant</Badge>}
                      {spl.compliance_status === 'Non-Compliant' && <Badge variant="destructive">Non-Compliant</Badge>}
                      {!spl.compliance_status && <span className="text-muted-foreground">-</span>}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        <FileCheck className="h-4 w-4 mr-1" /> Report
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Create Campaign Dialog */}
      <Dialog open={isCampaignDialogOpen} onOpenChange={setIsCampaignDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Create Sampling Campaign</DialogTitle>
            <DialogDescription>
              Create a new sampling campaign to organize sample collection.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Campaign Name</Label>
              <Input
                placeholder="e.g., Q1 2026 Routine Sampling"
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

      {/* Register Sample Dialog */}
      <Dialog open={isSampleDialogOpen} onOpenChange={setIsSampleDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Register New Sample</DialogTitle>
            <DialogDescription>
              Register a new sample for laboratory analysis.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Sample ID</Label>
              <Input
                placeholder="e.g., SPL-2026-001"
                value={newSample.sample_id}
                onChange={e => setNewSample({ ...newSample, sample_id: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Type</Label>
                <Select
                  value={newSample.type}
                  onValueChange={(v) => setNewSample({ ...newSample, type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Oil">Oil</SelectItem>
                    <SelectItem value="Gas">Gas</SelectItem>
                    <SelectItem value="Water">Water</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Campaign</Label>
                <Select
                  value={newSample.campaign_id.toString()}
                  onValueChange={(v) => setNewSample({ ...newSample, campaign_id: parseInt(v) })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select campaign" />
                  </SelectTrigger>
                  <SelectContent>
                    {campaigns.map(c => (
                      <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Collection Location</Label>
              <Input
                placeholder="e.g., Oil Export Header"
                value={newSample.location}
                onChange={e => setNewSample({ ...newSample, location: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Collection Date</Label>
                <Input
                  type="date"
                  value={newSample.collection_date}
                  onChange={e => setNewSample({ ...newSample, collection_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Responsible</Label>
                <Input
                  placeholder="Engineer name"
                  value={newSample.responsible}
                  onChange={e => setNewSample({ ...newSample, responsible: e.target.value })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleCreateSample}>Register Sample</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
