import React, { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Trash2, ShieldCheck, Settings2, RefreshCw } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export function AttributeRules() {
  const [attributes, setAttributes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isAdding, setIsAdding] = useState(false)

  // New Attribute State
  const [name, setName] = useState("")
  const [desc, setDesc] = useState("")
  const [type, setType] = useState("Text")
  const [unit, setUnit] = useState("")
  const [rules, setRules] = useState("")

  const loadAttributes = async () => {
    setLoading(true)
    try {
      const res = await apiFetch("/config/attributes")
      if (res.ok) {
        setAttributes(await res.json())
      } else {
        toast.error("Failed to load attribute definitions")
      }
    } catch (err) {
      toast.error("Failed to load attribute definitions")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAttributes()
  }, [])

  const handleCreate = async () => {
    try {
      if (!name) return
      const res = await apiFetch("/config/attributes", {
        method: "POST",
        body: JSON.stringify({
          name,
          description: desc,
          type,
          unit,
          validation_rules: rules,
          entity_type: "DEVICE_TYPE" // Default for now
        })
      })

      if (res.ok) {
        toast.success("Attribute defined successfully")
        setIsAdding(false)
        setName("")
        setDesc("")
        setType("Text")
        setUnit("")
        setRules("")
        loadAttributes()
      } else {
        throw new Error("Failed")
      }
    } catch (error) {
      toast.error("Failed to define attribute")
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="space-y-1">
            <CardTitle>Dynamic Attribute Definitions</CardTitle>
            <CardDescription>Define custom fields and their validation rules for assets.</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={loadAttributes}>
              <RefreshCw className="h-4 w-4 mr-2" /> Refresh
            </Button>
            <Dialog open={isAdding} onOpenChange={setIsAdding}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" /> New Attribute
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Define New Attribute</DialogTitle>
                  <DialogDescription>Attributes can be assigned to different levels of the asset hierarchy.</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="name" className="text-right">Name</Label>
                    <Input id="name" value={name} onChange={(e) => setName(e.target.value)} className="col-span-3" />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="type" className="text-right">Type</Label>
                    <Select value={type} onValueChange={setType}>
                      <SelectTrigger className="col-span-3">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Text">Text</SelectItem>
                        <SelectItem value="Date">Date</SelectItem>
                        <SelectItem value="Numerical">Numerical</SelectItem>
                        <SelectItem value="Multiple Choice">Multiple Choice</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="unit" className="text-right">Unit</Label>
                    <Input id="unit" value={unit} onChange={(e) => setUnit(e.target.value)} className="col-span-3" placeholder="e.g. %, °C, bar" />
                  </div>

                  <div className="border-t pt-4 mt-2">
                    <Label className="text-[10px] font-bold uppercase text-muted-foreground mb-4 block">Validation Rules (Engine V1)</Label>
                    {type === "Numerical" ? (
                      <div className="grid grid-cols-2 gap-4 ml-4">
                        <div className="space-y-1">
                          <Label className="text-[10px]">Min Value</Label>
                          <Input
                            type="number"
                            placeholder="0"
                            onChange={(e) => {
                              const v = e.target.value
                              if (!v) return
                              try {
                                const current = rules ? JSON.parse(rules) : {}
                                setRules(JSON.stringify({ ...current, min: parseFloat(v) }))
                              } catch (e) {
                                setRules(JSON.stringify({ min: parseFloat(v) }))
                              }
                            }}
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-[10px]">Max Value</Label>
                          <Input
                            type="number"
                            placeholder="100"
                            onChange={(e) => {
                              const v = e.target.value
                              if (!v) return
                              try {
                                const current = rules ? JSON.parse(rules) : {}
                                setRules(JSON.stringify({ ...current, max: parseFloat(v) }))
                              } catch (e) {
                                setRules(JSON.stringify({ max: parseFloat(v) }))
                              }
                            }}
                          />
                        </div>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 gap-4 ml-4">
                        <div className="space-y-1">
                          <Label className="text-[10px]">Min Length</Label>
                          <Input
                            type="number"
                            placeholder="5"
                            onChange={(e) => {
                              const v = e.target.value
                              if (!v) return
                              try {
                                const current = rules ? JSON.parse(rules) : {}
                                setRules(JSON.stringify({ ...current, min_length: parseInt(v) }))
                              } catch (e) {
                                setRules(JSON.stringify({ min_length: parseInt(v) }))
                              }
                            }}
                          />
                        </div>
                      </div>
                    )}
                    <div className="mt-2 ml-4">
                      <Label className="text-[10px]">Raw JSON (Advanced)</Label>
                      <Input
                        value={rules}
                        onChange={(e) => setRules(e.target.value)}
                        className="font-mono text-[10px] h-8"
                        placeholder='{"custom": true}'
                      />
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAdding(false)}>Cancel</Button>
                  <Button onClick={handleCreate}>Save Definition</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <div className="relative overflow-x-auto border rounded-md min-h-[100px]">
            {loading ? (
              <div className="p-8 text-center text-sm text-muted-foreground animate-pulse">Loading definitions...</div>
            ) : attributes.length === 0 ? (
              <div className="p-8 text-center text-sm text-muted-foreground">No custom attributes defined.</div>
            ) : (
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/50">
                  <tr>
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Rules</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {attributes.map((attr) => (
                    <tr key={attr.id} className="border-b hover:bg-muted/20 transition-colors">
                      <td className="px-4 py-3 font-medium">
                        <div className="flex flex-col">
                          <span>{attr.name}</span>
                          <span className="text-xs text-muted-foreground font-normal">{attr.unit}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="bg-primary/10 text-primary text-[10px] font-bold px-2 py-0.5 rounded uppercase">
                          {attr.type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <ShieldCheck className="h-3 w-3 text-green-600" />
                          <span className="text-xs">
                            {typeof attr.validation_rules === 'object'
                              ? JSON.stringify(attr.validation_rules)
                              : (attr.validation_rules || "No rules")}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" className="h-8 w-8"><Settings2 className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive"><Trash2 className="h-4 w-4" /></Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-orange-50/30 border-orange-100">
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Settings2 className="h-4 w-4 text-orange-600" />
            Rule Configuration Logic
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground">
          Validation rules follow the format specified in the Functional Specification.
          Admins can chain rules with <b>AND/OR</b> logic (e.g., [Value &gt; 0] AND [Mandatory if System Type = Ultrasonic]).
        </CardContent>
      </Card>
    </div>
  )
}
