"use client"

import React, { useState, useEffect } from "react"
import { ChevronRight, ChevronDown, Package, Layers, Cpu, Radio, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface Node {
  id: number
  tag: string
  description: string
  level_type: string
  children?: Node[]
}

const levelIcons: Record<string, any> = {
  FPSO: Layers,
  System: Package,
  Variable: Cpu,
  Device: Radio,
}

const TreeNode = ({ node, level = 0 }: { node: Node; level: number }) => {
  const [isOpen, setIsOpen] = useState(false)
  const Icon = levelIcons[node.level_type] || Package
  const hasChildren = node.children && node.children.length > 0

  return (
    <div className="select-none">
      <div 
        className={cn(
          "flex items-center gap-2 px-2 py-1.5 hover:bg-muted/50 rounded-sm cursor-pointer group transition-colors",
          level === 0 && "font-bold text-primary"
        )}
        onClick={() => setIsOpen(!isOpen)}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
      >
        {hasChildren ? (
          isOpen ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />
        ) : (
          <div className="w-4" />
        )}
        <Icon className={cn("h-4 w-4", level === 0 ? "text-primary" : "text-muted-foreground")} />
        <span className="text-sm">{node.tag}</span>
        <span className="text-xs text-muted-foreground truncate opacity-0 group-hover:opacity-100 transition-opacity ml-2">
          - {node.description}
        </span>
        <div className="ml-auto flex items-center gap-1 opacity-0 group-hover:opacity-100">
          <Button variant="ghost" size="icon" className="h-6 w-6"><Plus className="h-3 w-3" /></Button>
          <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive"><Trash2 className="h-3 w-3" /></Button>
        </div>
      </div>
      
      {isOpen && hasChildren && (
        <div className="border-l border-muted ml-4">
          {node.children!.map((child) => (
            <TreeNode key={child.id} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export function HierarchyTree() {
  const [data, setData] = useState<Node[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("http://localhost:8000/api/config/hierarchy/tree")
      .then(res => res.json())
      .then(json => {
        setData(Array.isArray(json) ? json : [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Failed to fetch tree:", err)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="p-4 text-sm text-muted-foreground">Loading tree...</div>
  
  if (data.length === 0) return (
    <div className="p-8 text-center border-2 border-dashed rounded-lg">
      <p className="text-sm text-muted-foreground mb-4">No hierarchy modeled yet.</p>
      <Button variant="outline" size="sm">
        <Plus className="h-4 w-4 mr-2" /> Start Modeling FPSO
      </Button>
    </div>
  )

  return (
    <div className="border rounded-md bg-white overflow-hidden shadow-sm">
      <div className="bg-muted/30 p-2 border-b flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-2">Asset Hierarchy</span>
        <Button variant="ghost" size="sm" className="h-7 text-xs">Collapse All</Button>
      </div>
      <div className="p-2 max-h-[600px] overflow-auto">
        {data.map(node => (
          <TreeNode key={node.id} node={node} level={0} />
        ))}
      </div>
    </div>
  )
}
