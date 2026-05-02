"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export function ValidationLimits() {
  const [params, setParams] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const loadParams = async () => {
    try {
      const res = await apiFetch("/config/parameters")
      if (res.ok) {
        setParams(await res.json())
      }
    } catch (error) {
      toast.error("Failed to load parameters")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadParams()
  }, [])

  const getParamValue = (key: string, defaultValue: string) => {
    return params.find((p) => p.key === key)?.value || defaultValue
  }

  const handleSaveParam = async (key: string, value: string, description: string) => {
    try {
      const res = await apiFetch("/config/parameters", {
        method: "POST",
        body: JSON.stringify({ key, value, fpso: "GLOBAL", description }),
      })
      if (res.ok) {
        toast.success(`${key} updated successfully`)
        loadParams()
      } else {
        throw new Error("Failed to update parameter")
      }
    } catch (error) {
      toast.error("Failed to update parameter")
    }
  }

  if (loading) return <div>Loading validation limits...</div>

  return (
    <Card>
      <CardHeader>
        <CardTitle>Validation & Statistical Limits</CardTitle>
        <CardDescription>
          Global parameters used by the automated report validation engine. Adjusting these will immediately affect how future lab reports are approved or reproved.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label>Sigma Multiplier (σ)</Label>
            <Input
              type="number"
              step="0.1"
              defaultValue={getParamValue("SIGMA_MULTIPLIER", "2")}
              onBlur={(e) =>
                handleSaveParam(
                  "SIGMA_MULTIPLIER",
                  e.target.value,
                  "Standard deviations for acceptance band in historical analysis."
                )
              }
            />
            <p className="text-xs text-muted-foreground">Standard deviations used for acceptance bands (typically 2.0).</p>
          </div>
          
          <div className="space-y-2">
            <Label>History Size</Label>
            <Input
              type="number"
              defaultValue={getParamValue("HISTORY_SIZE", "10")}
              onBlur={(e) =>
                handleSaveParam(
                  "HISTORY_SIZE",
                  e.target.value,
                  "Number of past samples used to compute historical mean and variance."
                )
              }
            />
            <p className="text-xs text-muted-foreground">Number of past valid samples to evaluate against.</p>
          </div>
        </div>

        <div className="border-t pt-4 mt-4">
          <h3 className="font-semibold mb-4 text-sm">Hard Limits (Chemical)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label>O₂ Hard Limit (%)</Label>
              <Input
                type="number"
                step="0.01"
                defaultValue={getParamValue("VALIDATION_LIMIT_O2", "0.5")}
                onBlur={(e) =>
                  handleSaveParam(
                    "VALIDATION_LIMIT_O2",
                    e.target.value,
                    "Maximum allowable O2 percentage. Reproves if exceeded."
                  )
                }
              />
              <p className="text-xs text-destructive">Reprovatory if exceeded</p>
            </div>

            <div className="space-y-2">
              <Label>H₂S Limit (ppm)</Label>
              <Input
                type="number"
                step="0.1"
                defaultValue={getParamValue("VALIDATION_LIMIT_H2S", "10.0")}
                onBlur={(e) =>
                  handleSaveParam(
                    "VALIDATION_LIMIT_H2S",
                    e.target.value,
                    "H2S limit in ppm. Currently informative."
                  )
                }
              />
              <p className="text-xs text-muted-foreground">Informative only</p>
            </div>

            <div className="space-y-2">
              <Label>BS&W Limit (%)</Label>
              <Input
                type="number"
                step="0.1"
                defaultValue={getParamValue("VALIDATION_LIMIT_BSW", "1.0")}
                onBlur={(e) =>
                  handleSaveParam(
                    "VALIDATION_LIMIT_BSW",
                    e.target.value,
                    "BSW limit percentage. Currently informative."
                  )
                }
              />
              <p className="text-xs text-muted-foreground">Informative only</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
