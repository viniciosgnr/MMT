import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { Loader2, Save, Link2 } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { Badge } from "@/components/ui/badge"

interface AttributeDefinition {
  id: number
  name: string
  description: string
  type: string
  unit?: string
}

interface AttributeValue {
  attribute_id: number
  value: string
}

interface PropertyEditorProps {
  nodeId: number | null
  nodeTag: string | null
  selectedNode?: any
}

export function PropertyEditor({ nodeId, nodeTag, selectedNode }: PropertyEditorProps) {
  const [definitions, setDefinitions] = useState<AttributeDefinition[]>([])
  const [values, setValues] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  // Real-time Module 1 Sync State
  const [m1TagData, setM1TagData] = useState<any | null>(null)
  const [m1Loading, setM1Loading] = useState(false)

  useEffect(() => {
    if (nodeId) {
      loadData()
    }
  }, [nodeId])

  const loadData = async () => {
    setLoading(true)
    try {
      // 1. Fetch all definitions (Ideally filtered by entity_type, but for now all)
      const defRes = await apiFetch("/config/attributes")
      const valRes = await apiFetch(`/config/values/${nodeId}`)

      if (defRes.ok && valRes.ok) {
        const defData = await defRes.json()
        setDefinitions(defData)

        const valData: AttributeValue[] = await valRes.json()

        const valMap: Record<number, string> = {}
        valData.forEach(v => {
          valMap[v.attribute_id] = v.value
        })
        setValues(valMap)
      } else {
        toast.error("Failed to load property data")
      }
    } catch (error) {
      toast.error("Failed to load property data")
    } finally {
      setLoading(false)
    }
  }

  const loadM1Data = async (tagName: string) => {
    setM1Loading(true)
    setM1TagData(null)
    try {
      // Bust cache to always get latest installations and increase limit
      const res = await apiFetch(`/equipment/tags?limit=1000&tag_number=${tagName}&t=${new Date().getTime()}`)
      if (res.ok) {
        const data = await res.json()
        // If an exact match is returned, save it
        if (data && data.length > 0) {
          const matchedTag = data.find((t: any) => t.tag_number === tagName)
          if (matchedTag) {
            setM1TagData(matchedTag)
          }
        }
      }
    } catch (e) {
      console.error("Failed to load M1 linked data:", e)
    } finally {
      setM1Loading(false)
    }
  }

  useEffect(() => {
    if (nodeTag) {
      // Only fetch M1 data if looking at an instrument (heuristic: tag matches PT/TT/TE/AP/FT)
      if (nodeTag.match(/-(PT|TT|TE|AP|FT)-/) || nodeTag.match(/-(PT|TT|TE|AP|FT)$/)) {
        loadM1Data(nodeTag)
      } else {
        setM1TagData(null)
      }
    } else {
      setM1TagData(null)
    }
  }, [nodeTag])



  const handleSave = async (attrId: number) => {
    setSaving(true)
    try {
      const res = await apiFetch("/config/values", {
        method: "POST",
        body: JSON.stringify({
          attribute_id: attrId,
          entity_id: nodeId,
          value: values[attrId] || ""
        })
      })

      if (res.ok) {
        toast.success("Property updated")
      } else {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || "Validation failed")
      }
    } catch (error: any) {
      toast.error(error.message || "Validation failed")
    } finally {
      setSaving(false)
    }
  }

  if (!nodeId) {
    return (
      <Card className="h-full flex items-center justify-center text-muted-foreground border-dashed">
        <p>Select a node in the hierarchy to edit properties.</p>
      </Card>
    )
  }

  const validAttributes = selectedNode?.attributes
    ? Object.entries(selectedNode.attributes).filter(([k]) => k !== "analysis_types")
    : [];

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Properties: {nodeTag}
          {m1TagData && (
            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
              <Link2 className="w-3 h-3 mr-1" />
              M1 Active
            </Badge>
          )}
        </CardTitle>
        <CardDescription>Configure specific attributes for this node.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">

        {/* Module 1 Integrated Real-time Data Block */}
        {m1Loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground p-4 bg-slate-50 rounded-lg">
            <Loader2 className="h-4 w-4 animate-spin" />
            Retrieving Module 1 status...
          </div>
        )}
        {!m1Loading && m1TagData && (
          <div className="space-y-3 p-4 bg-emerald-50/50 rounded-lg border border-emerald-100">
            <div className="flex justify-between items-center mb-2 border-b border-emerald-100/50 pb-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800">Linked Equipment (M1)</h4>
              {m1TagData.installations?.find((i: any) => i.is_active) ? (
                <Badge className="bg-emerald-500 text-white text-[10px]">Installed</Badge>
              ) : (
                <Badge variant="secondary" className="text-[10px]">Not Installed</Badge>
              )}
            </div>

            <div className="grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
              <div className="flex flex-col">
                <span className="text-emerald-600/70 text-[10px] uppercase font-bold tracking-wider">M1 Description</span>
                <span className="font-medium text-emerald-950 truncate" title={m1TagData.description}>{m1TagData.description}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-emerald-600/70 text-[10px] uppercase font-bold tracking-wider">Area / Service</span>
                <span className="font-medium text-emerald-950">{m1TagData.area || 'N/A'}</span>
              </div>

              {(() => {
                const active = m1TagData.installations?.find((i: any) => i.is_active);
                if (active && active.equipment) {
                  return (
                    <>
                      <div className="flex flex-col">
                        <span className="text-emerald-600/70 text-[10px] uppercase font-bold tracking-wider">Serial Number</span>
                        <span className="font-medium text-emerald-950 font-mono tracking-tight">{active.equipment.serial_number}</span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-emerald-600/70 text-[10px] uppercase font-bold tracking-wider">Manufacturer / Model</span>
                        <span className="font-medium text-emerald-950 truncate" title={`${active.equipment.manufacturer} - ${active.equipment.model}`}>
                          {active.equipment.manufacturer} <span className="text-emerald-800/60 font-normal">({active.equipment.model})</span>
                        </span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-emerald-600/70 text-[10px] uppercase font-bold tracking-wider">Installation Date</span>
                        <span className="font-medium text-emerald-950">{new Date(active.installation_date).toLocaleDateString()}</span>
                      </div>
                      {active.equipment.calibration_frequency_months && (
                        <div className="flex flex-col">
                          <span className="text-emerald-600/70 text-[10px] uppercase font-bold tracking-wider">M1 Cal. Freq.</span>
                          <span className="font-medium text-emerald-950">{active.equipment.calibration_frequency_months} Months</span>
                        </div>
                      )}
                    </>
                  )
                }
                return null;
              })()}
            </div>
          </div>
        )}
        {validAttributes.length > 0 && (
          <div className="space-y-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
            <h4 className="text-sm font-semibold text-slate-800">Asset Specifications</h4>
            <div className="grid grid-cols-2 gap-4 text-sm mt-2">
              {validAttributes.map(([key, val]) => (
                <div key={key} className="flex flex-col">
                  <span className="text-slate-500 text-[10px] tracking-wider uppercase font-bold">{key.replace('_', ' ')}</span>
                  <span className="font-medium text-slate-900 mt-0.5">
                    {Array.isArray(val) ? val.join(", ") : String(val)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : definitions.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">No dynamic attributes defined.</p>
        ) : (
          definitions.map(def => (
            <div key={def.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={`attr-${def.id}`}>{def.name} {def.unit && `(${def.unit})`}</Label>
                <div className="text-[10px] bg-secondary px-1.5 py-0.5 rounded uppercase font-bold text-secondary-foreground">
                  {def.type}
                </div>
              </div>
              <div className="flex gap-2">
                <Input
                  id={`attr-${def.id}`}
                  value={values[def.id] || ""}
                  onChange={(e) => setValues({ ...values, [def.id]: e.target.value })}
                  placeholder={def.description || `Enter ${def.name.toLowerCase()}...`}
                />
                <Button
                  size="icon"
                  variant="outline"
                  onClick={() => handleSave(def.id)}
                  disabled={saving}
                >
                  <Save className="h-4 w-4" />
                </Button>
              </div>
              {def.description && (
                <p className="text-[11px] text-muted-foreground">{def.description}</p>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
