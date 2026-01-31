import React, { useState, useEffect, useCallback } from "react"
import { ChevronRight, ChevronDown, Package, Layers, Cpu, Radio, Plus, Trash2, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { fetchHierarchyTree, createHierarchyNode, deleteHierarchyNode } from "@/lib/api"
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

const nextLevel: Record<string, string> = {
  "ROOT": "FPSO",
  "FPSO": "System",
  "System": "Variable",
  "Variable": "Device",
}

interface HierarchyTreeProps {
  onSelect?: (nodeId: number, nodeTag: string) => void
  selectedId?: number | null
}

const TreeNode = ({
  node,
  level = 0,
  onRefresh,
  onSelect,
  selectedId
}: {
  node: Node;
  level: number;
  onRefresh: () => void;
  onSelect?: (id: number, tag: string) => void
  selectedId?: number | null
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isAdding, setIsAdding] = useState(false)
  const [newTag, setNewTag] = useState("")
  const [newDesc, setNewDesc] = useState("")

  const Icon = levelIcons[node.level_type] || Package
  const hasChildren = node.children && node.children.length > 0
  const nextTarget = nextLevel[node.level_type]

  const handleCreate = async () => {
    try {
      if (!newTag) return
      await createHierarchyNode({
        tag: newTag,
        description: newDesc,
        level_type: nextTarget,
        parent_id: node.id
      })
      toast.success(`${nextTarget} created successfully`)
      setIsAdding(false)
      setNewTag("")
      setNewDesc("")
      onRefresh()
      setIsOpen(true)
    } catch (error) {
      toast.error("Failed to create node")
    }
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(`Are you sure you want to delete ${node.tag}?`)) return
    try {
      await deleteHierarchyNode(node.id)
      toast.success("Node deleted successfully")
      onRefresh()
    } catch (error: any) {
      toast.error(error.message || "Failed to delete node")
    }
  }

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-2 px-2 py-1.5 hover:bg-muted/50 rounded-sm cursor-pointer group transition-colors",
          level === 0 && "font-bold text-primary",
          selectedId === node.id && "bg-primary/10 ring-1 ring-primary/30"
        )}
        onClick={() => {
          setIsOpen(!isOpen)
          onSelect?.(node.id, node.tag)
        }}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
      >
        {hasChildren ? (
          isOpen ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />
        ) : (
          <div className="w-4" />
        )}
        <Icon className={cn("h-4 w-4", level === 0 ? "text-primary" : "text-muted-foreground")} />
        <div className="flex flex-col">
          <span className="text-sm">{node.tag}</span>
          {node.description && <span className="text-[10px] text-muted-foreground leading-none">{node.description}</span>}
        </div>

        <div className="ml-auto flex items-center gap-1 opacity-0 group-hover:opacity-100">
          {nextTarget && (
            <Dialog open={isAdding} onOpenChange={setIsAdding}>
              <DialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={(e) => {
                    e.stopPropagation()
                    setIsAdding(true)
                  }}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </DialogTrigger>
              <DialogContent onClick={(e) => e.stopPropagation()}>
                <DialogHeader>
                  <DialogTitle>Add {nextTarget}</DialogTitle>
                  <DialogDescription>Create a new {nextTarget} under {node.tag}.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="tag">Tag / Short Name</Label>
                    <Input id="tag" placeholder="e.g. FPSO SEPETIBA" value={newTag} onChange={(e) => setNewTag(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Input id="description" placeholder="Optional details..." value={newDesc} onChange={(e) => setNewDesc(e.target.value)} />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAdding(false)}>Cancel</Button>
                  <Button onClick={handleCreate}>Create</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
          <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={handleDelete}><Trash2 className="h-3 w-3" /></Button>
        </div>
      </div>

      {isOpen && hasChildren && (
        <div className="border-l border-muted ml-4">
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onRefresh={onRefresh}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function HierarchyTree({ onSelect, selectedId }: HierarchyTreeProps) {
  const [data, setData] = useState<Node[]>([])
  const [loading, setLoading] = useState(true)
  const [isAddingRoot, setIsAddingRoot] = useState(false)
  const [newTag, setNewTag] = useState("")

  const loadTree = useCallback(async () => {
    setLoading(true)
    try {
      const tree = await fetchHierarchyTree()
      setData(tree)
    } catch (err) {
      console.error("Failed to fetch tree:", err)
      toast.error("Failed to load asset hierarchy")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTree()
  }, [loadTree])

  const handleCreateRoot = async () => {
    try {
      if (!newTag) return
      await createHierarchyNode({
        tag: newTag,
        description: "",
        level_type: "FPSO",
        parent_id: null
      })
      toast.success("FPSO created successfully")
      setIsAddingRoot(false)
      setNewTag("")
      loadTree()
    } catch (error) {
      toast.error("Failed to create FPSO")
    }
  }

  if (loading) return (
    <div className="p-8 flex items-center justify-center text-sm text-muted-foreground animate-pulse">
      <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Fetching asset hierarchy...
    </div>
  )

  if (data.length === 0) return (
    <div className="p-8 text-center border-2 border-dashed rounded-lg bg-muted/5">
      <p className="text-sm text-muted-foreground mb-4">No hierarchy modeled yet.</p>
      <Dialog open={isAddingRoot} onOpenChange={setIsAddingRoot}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm">
            <Plus className="h-4 w-4 mr-2" /> Start Modeling FPSO
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Start Modeling</DialogTitle>
            <DialogDescription>Create the root node (FPSO) for your asset hierarchy.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="root-tag">FPSO Name</Label>
              <Input id="root-tag" placeholder="e.g. FPSO SEPETIBA" value={newTag} onChange={(e) => setNewTag(e.target.value)} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddingRoot(false)}>Cancel</Button>
            <Button onClick={handleCreateRoot}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )

  return (
    <div className="border rounded-md bg-white overflow-hidden shadow-sm">
      <div className="bg-muted/30 p-2 border-b flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-2">Asset Hierarchy Browser</span>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={loadTree}><RefreshCw className="h-3 w-3 mr-1" /> Refresh</Button>
          <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => setIsAddingRoot(true)}><Plus className="h-3 w-3 mr-1" /> Add FPSO</Button>
        </div>
      </div>
      <div className="p-2 max-h-[600px] overflow-auto">
        {data.map(node => (
          <TreeNode
            key={node.id}
            node={node}
            level={0}
            onRefresh={loadTree}
            onSelect={onSelect}
            selectedId={selectedId}
          />
        ))}
      </div>
    </div>
  )
}
