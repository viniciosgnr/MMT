"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Save, ShieldCheck } from "lucide-react"
import { toast } from "sonner"
import { format } from "date-fns"

export default function EditFailurePage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState<any>(null)

  useEffect(() => {
    async function fetchFailure() {
      try {
        const res = await apiFetch(`/failures/${id}`)
        if (res.ok) {
          const failure = await res.json()
          setFormData(failure)
        } else {
          if (res.status === 404) {
            toast.error("Failure not found")
            router.push("/dashboard/failure-notification")
          } else {
            // If not JSON, we might get syntax error here if we don't handle it
            const text = await res.text()
            try {
              const errorJson = JSON.parse(text)
              toast.error(errorJson.detail || "Error loading failure")
            } catch {
              console.error("API Error (Non-JSON):", text)
              toast.error(`API Error: ${res.statusText}`)
            }
          }
        }
      } catch (error) {
        toast.error("Error loading failure details")
      } finally {
        setLoading(false)
      }
    }
    fetchFailure()
  }, [id, router])

  const handleSave = async () => {
    // Mock save
    toast.success("Changes saved successfully")
  }

  const handleApprove = async () => {
    try {
      const res = await apiFetch(`/failures/${id}/approve`, {
        method: "POST",
        body: JSON.stringify({ approved_by: "Marcos G. (ME)" })
      })
      if (res.ok) {
        toast.success("Approved! Reports sent.")
        setFormData({ ...formData, status: "Approved" })
      }
    } catch (e) { toast.error("Approval failed") }
  }

  if (loading) return <div className="p-8 text-center text-muted-foreground">Loading failure details...</div>

  if (!formData) return (
    <div className="p-8 flex flex-col items-center gap-4">
      <div className="text-red-500 font-medium">Failure #{id} not found.</div>
      <Button variant="outline" onClick={() => router.push('/dashboard/failure-notification')}>
        <ArrowLeft className="mr-2 h-4 w-4" /> Return to List
      </Button>
    </div>
  )

  return (
    <div className="space-y-6 max-w-4xl mx-auto py-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#003D5C]">
            Failure Details #{formData.id}
          </h1>
          <p className="text-muted-foreground flex items-center gap-2">
            Status: <span className="font-semibold">{formData.status}</span>
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Report Details</CardTitle>
          <CardDescription>View and edit failure information.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>FPSO</Label>
              <Input value={formData.fpso_name || ""} disabled />
            </div>
            <div className="space-y-2">
              <Label>Eq. Tag</Label>
              <Input value={formData.tag || ""} disabled />
            </div>
            <div className="space-y-2">
              <Label>Failure Date</Label>
              <Input value={formData.failure_date?.slice(0, 16) || ""} onChange={(e) => setFormData({ ...formData, failure_date: e.target.value })} type="datetime-local" />
            </div>
            <div className="space-y-2">
              <Label>ANP Classification</Label>
              <Select value={formData.anp_classification || ""} onValueChange={(v) => setFormData({ ...formData, anp_classification: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Tolerável">Tolerável</SelectItem>
                  <SelectItem value="Grave">Grave</SelectItem>
                  <SelectItem value="Crítica">Crítica</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Description</Label>
            <Textarea
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label>Corrective Action</Label>
            <Textarea
              value={formData.corrective_action || ""}
              onChange={(e) => setFormData({ ...formData, corrective_action: e.target.value })}
              rows={4}
            />
          </div>
        </CardContent>
        <CardFooter className="bg-slate-50 justify-between">
          <Button variant="outline" onClick={() => router.back()}>Cancel</Button>
          <div className="flex gap-2">
            <Button variant="default" onClick={handleSave} className="bg-[#003D5C]">
              <Save className="mr-2 h-4 w-4" /> Save Changes
            </Button>
            {formData.status === 'Draft' && (
              <Button variant="outline" onClick={handleApprove} className="text-green-600 border-green-200 hover:bg-green-50">
                <ShieldCheck className="mr-2 h-4 w-4" /> Approve & Send
              </Button>
            )}
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
