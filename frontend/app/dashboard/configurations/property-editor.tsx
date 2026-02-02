import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { Loader2, Save } from "lucide-react"
import { apiFetch } from "@/lib/api"

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
}

export function PropertyEditor({ nodeId, nodeTag }: PropertyEditorProps) {
  const [definitions, setDefinitions] = useState<AttributeDefinition[]>([])
  const [values, setValues] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

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

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Properties: {nodeTag}</CardTitle>
        <CardDescription>Configure specific attributes for this node.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
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
