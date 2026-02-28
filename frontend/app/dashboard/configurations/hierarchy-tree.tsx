import React, { useState, useEffect, useCallback } from "react"
import { ChevronRight, ChevronDown, Package, Layers, Cpu, Radio, Plus, Trash2, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface Node {
  id: number
  tag: string
  description: string
  level_type: string
  attributes?: Record<string, any>
  children?: Node[]
}

const levelIcons: Record<string, any> = {
  "FPSO": Layers,
  "Sample Point": Package,
  "Metering Point": Cpu,
}

const nextLevel: Record<string, string> = {
  "ROOT": "FPSO",
  "FPSO": "Metering Point",
  "Metering Point": "Sample Point",
}

interface HierarchyTreeProps {
  onSelect?: (node: Node) => void
  selectedId?: number | null
  initialNodeId?: number | null
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
  onSelect?: (node: Node) => void
  selectedId?: number | null
}) => {
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    if (selectedId && node.children) {
      const hasSelectedDescendant = (n: Node, id: number): boolean => {
        if (!n.children) return false;
        return n.children.some(c => c.id === id || hasSelectedDescendant(c, id));
      };
      if (hasSelectedDescendant(node, selectedId)) {
        setIsOpen(true);
      }
    }
  }, [selectedId, node]);

  const [isAdding, setIsAdding] = useState(false)
  const [newTag, setNewTag] = useState("")
  const [newDesc, setNewDesc] = useState("")
  const [newClassification, setNewClassification] = useState("")

  const Icon = levelIcons[node.level_type] || Package
  const hasChildren = node.children && node.children.length > 0
  const nextTarget = nextLevel[node.level_type]

  const handleCreate = async () => {
    try {
      if (!newTag) return
      const res = await apiFetch("/config/hierarchy/nodes", {
        method: "POST",
        body: JSON.stringify({
          tag: newTag,
          description: newDesc,
          level_type: nextTarget,
          parent_id: node.id,
          attributes: nextTarget === "Metering Point" && newClassification ? { classification: newClassification } : undefined
        })
      })

      if (res.ok) {
        toast.success(`${nextTarget} created successfully`)
        setIsAdding(false)
        setNewTag("")
        setNewDesc("")
        setNewClassification("")
        onRefresh()
        window.dispatchEvent(new Event("hierarchy-updated"))
        setIsOpen(true)
      } else {
        throw new Error("Failed")
      }
    } catch (error) {
      toast.error("Failed to create node")
    }
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(`Are you sure you want to delete ${node.tag}?`)) return
    try {
      const res = await apiFetch(`/config/hierarchy/nodes/${node.id}`, { method: "DELETE" })
      if (res.ok) {
        toast.success("Node deleted successfully")
        onRefresh()
        window.dispatchEvent(new Event("hierarchy-updated"))
      } else {
        throw new Error("Failed")
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to delete node")
    }
  }

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-2 px-2 py-1.5 hover:bg-muted/50 rounded-sm group transition-colors",
          node.level_type === "Sample Point" ? "cursor-default" : "cursor-pointer",
          level === 0 && "font-bold text-primary",
          selectedId === node.id && node.level_type !== "Sample Point" && "bg-primary/10 ring-1 ring-primary/30"
        )}
        onClick={() => {
          setIsOpen(!isOpen)
          if (node.level_type !== "Sample Point") {
            onSelect?.(node)
          }
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
          <div className="flex items-center gap-2">
            <span className="text-sm">{node.tag}</span>
            {node.attributes?.classification && (() => {
              const clsMap: Record<string, string> = {
                "Fiscal": "bg-blue-100 text-blue-700",
                "Custody Transfer": "bg-indigo-100 text-indigo-700",
                "Apropriation": "bg-purple-100 text-purple-700",
                "Operational": "bg-slate-100 text-slate-600",
              };
              const cClass = clsMap[node.attributes.classification] || "bg-gray-100 text-gray-700";
              return (
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap ${cClass}`}>
                  {node.attributes.classification}
                </span>
              )
            })()}

          </div>
          {node.description && <span className="text-[10px] text-muted-foreground leading-none mt-1">{node.description}</span>}
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
                  {nextTarget === "Metering Point" && (
                    <div className="space-y-2">
                      <Label>Classification</Label>
                      <Select value={newClassification} onValueChange={setNewClassification}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select classification..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Fiscal">Fiscal</SelectItem>
                          <SelectItem value="Custody Transfer">Custody Transfer</SelectItem>
                          <SelectItem value="Apropriation">Apropriation</SelectItem>
                          <SelectItem value="Operational">Operational</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}
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

export function HierarchyTree({ onSelect, selectedId, initialNodeId }: HierarchyTreeProps) {
  const [data, setData] = useState<Node[]>([])
  const [loading, setLoading] = useState(true)
  const [isAddingRoot, setIsAddingRoot] = useState(false)
  const [newTag, setNewTag] = useState("")

  const loadTree = useCallback(async () => {
    setLoading(true)
    try {
      const res = await apiFetch(`/config/hierarchy/tree?_t=${Date.now()}`)
      if (res.ok) {
        const treeData = await res.json()
        setData(treeData)
      } else {
        throw new Error("Failed")
      }
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

  useEffect(() => {
    if (initialNodeId && initialNodeId !== selectedId && data.length > 0 && onSelect) {
      const findNode = (nodes: Node[]): Node | null => {
        for (const n of nodes) {
          if (n.id === initialNodeId) return n;
          if (n.children) {
            const found = findNode(n.children);
            if (found) return found;
          }
        }
        return null;
      }
      const foundNode = findNode(data)
      if (foundNode) {
        onSelect(foundNode)
      }
    }
  }, [initialNodeId, data]) // Exclude onSelect and selectedId to prevent infinite loops from non-memoized handlers

  const handleCreateRoot = async () => {
    try {
      if (!newTag) return
      const res = await apiFetch("/config/hierarchy/nodes", {
        method: "POST",
        body: JSON.stringify({
          tag: newTag,
          description: "",
          level_type: "FPSO",
          parent_id: null
        })
      })

      if (res.ok) {
        toast.success("FPSO created successfully")
        setIsAddingRoot(false)
        setNewTag("")
        loadTree()
      } else {
        throw new Error("Failed")
      }
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
          <Dialog open={isAddingRoot} onOpenChange={setIsAddingRoot}>
            <DialogTrigger asChild>
              <Button variant="default" size="sm" className="h-7 text-xs border-none text-white hover:opacity-90 transition-opacity" style={{ backgroundColor: "#f97316" }}><Plus className="h-3 w-3 mr-1" /> Add FPSO</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New FPSO</DialogTitle>
                <DialogDescription>Create a new root node (FPSO) for your asset hierarchy.</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="root-tag-main">FPSO Name</Label>
                  <Input id="root-tag-main" placeholder="e.g. FPSO ILHABELA" value={newTag} onChange={(e) => setNewTag(e.target.value)} />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddingRoot(false)}>Cancel</Button>
                <Button onClick={handleCreateRoot}>Create</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
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
