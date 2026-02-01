"use client"

import { useState, useEffect } from "react"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import {
  X,
  MessageSquare,
  Paperclip,
  Tag,
  Calendar,
  Link as LinkIcon,
  Trash2,
  Plus,
  Cpu,
  MapPin,
  ExternalLink,
  Save,
  User
} from "lucide-react"
import { toast } from "sonner"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

interface CardDetailsProps {
  cardId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpdated: () => void
}

export function CardDetails({ cardId, open, onOpenChange, onUpdated }: CardDetailsProps) {
  const [card, setCard] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [comment, setComment] = useState("")
  const [availableEquipment, setAvailableEquipment] = useState<any[]>([])
  const [availableTags, setAvailableTags] = useState<any[]>([])
  const [availableCards, setAvailableCards] = useState<any[]>([])
  const [isEditing, setIsEditing] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const fetchCard = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_URL}/maintenance/cards/${cardId}`)
      if (res.ok) setCard(await res.json())
    } catch (error) {
      toast.error("Failed to load card details")
    } finally {
      setLoading(false)
    }
  }

  const fetchOptions = async () => {
    try {
      const [eqRes, tagRes, cardRes] = await Promise.all([
        fetch(`${API_URL}/equipment`),
        fetch(`${API_URL}/equipment/tags`),
        fetch(`${API_URL}/maintenance/cards`)
      ])
      if (eqRes.ok) setAvailableEquipment(await eqRes.json())
      if (tagRes.ok) setAvailableTags(await tagRes.json())
      if (cardRes.ok) setAvailableCards(await cardRes.json())
    } catch (e) { }
  }

  useEffect(() => {
    if (open && cardId) {
      fetchCard()
      fetchOptions()
    }
  }, [open, cardId])

  const handleUpdate = async (updates: any) => {
    try {
      setSubmitting(true)
      const res = await fetch(`${API_URL}/maintenance/cards/${cardId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates)
      })
      if (res.ok) {
        toast.success("Card updated")
        fetchCard()
        onUpdated()
        setIsEditing(false)
      }
    } catch (error) {
      toast.error("Failed to update card")
    } finally {
      setSubmitting(false)
    }
  }

  const addComment = async () => {
    if (!comment.trim()) return
    try {
      const res = await fetch(`${API_URL}/maintenance/cards/${cardId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: comment, author: "Daniel Bernoulli" })
      })
      if (res.ok) {
        setComment("")
        fetchCard()
        onUpdated()
      }
    } catch (error) {
      toast.error("Failed to add comment")
    }
  }

  const linkEquipment = async (id: number) => {
    const currentIds = card.linked_equipments?.map((e: any) => e.id) || []
    if (currentIds.includes(id)) return
    handleUpdate({ equipment_ids: [...currentIds, id] })
  }

  const linkTag = async (id: number) => {
    const currentIds = card.linked_tags?.map((t: any) => t.id) || []
    if (currentIds.includes(id)) return
    handleUpdate({ tag_ids: [...currentIds, id] })
  }

  const linkCard = async (id: number) => {
    const currentIds = card.connections?.map((c: any) => c.id) || []
    if (currentIds.includes(id) || id === card.id) return
    handleUpdate({ connected_card_ids: [...currentIds, id] })
  }

  const unlinkCard = async (id: number) => {
    const currentIds = card.connections?.map((c: any) => c.id) || []
    const newIds = currentIds.filter((cid: number) => cid !== id)
    handleUpdate({ connected_card_ids: newIds })
  }

  if (loading && !card) return null

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[450px] sm:w-[550px] overflow-y-auto custom-scrollbar">
        <SheetHeader className="space-y-4">
          <div className="flex items-center justify-between mt-6">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[10px] font-bold uppercase tracking-wider bg-blue-50/50 text-blue-700 border-blue-200/50">
                {card?.fpso}
              </Badge>
              <Badge variant="secondary" className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 border-none">
                #{card?.id}
              </Badge>
            </div>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => onOpenChange(false)}>
              <X className="h-4 w-4 text-slate-400" />
            </Button>
          </div>

          <div className="space-y-1">
            <SheetTitle className="text-xl font-bold leading-tight">
              {card?.title}
            </SheetTitle>
            <SheetDescription>
              In column: <span className="font-medium text-slate-900 dark:text-slate-100">{card?.column?.name}</span>
            </SheetDescription>
          </div>
        </SheetHeader>

        <div className="mt-8 space-y-8 pb-10">
          {/* Card Properties Grid */}
          <div className="grid grid-cols-2 gap-y-4 text-sm">
            <div className="flex items-center gap-2 text-slate-500">
              <User className="h-4 w-4" />
              <span>Responsible</span>
            </div>
            <div className="font-medium">{card?.responsible || "Unassigned"}</div>

            <div className="flex items-center gap-2 text-slate-500">
              <Calendar className="h-4 w-4" />
              <span>Due Date</span>
            </div>
            <div className="font-medium">
              {card?.due_date ? new Date(card?.due_date).toLocaleDateString() : "No date"}
            </div>

            <div className="flex items-center gap-2 text-slate-500">
              <Tag className="h-4 w-4" />
              <span>Labels</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {card?.labels?.map((l: any) => (
                <Badge key={l.id} variant="secondary" style={{ borderLeft: `4px solid ${l.color}` }}>
                  {l.name}
                </Badge>
              ))}
              <Button variant="ghost" size="sm" className="h-6 p-1 text-[10px] gap-1">
                <Plus className="h-3 w-3" />
                Add
              </Button>
            </div>
          </div>

          <Separator />

          {/* Description */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
              <MessageSquare className="h-3.5 w-3.5" />
              Description
            </h3>
            <div className="bg-slate-50/50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-200/50 dark:border-slate-800/50 text-sm text-slate-700 dark:text-slate-300 min-h-[120px] leading-relaxed shadow-inner whitespace-pre-wrap">
              {card?.description || "No description provided. Click the edit icon to add context to this maintenance task."}
            </div>
          </div>

          {/* Linked Equipment */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Cpu className="h-4 w-4 text-blue-500" />
              Linked Equipment (S/N)
            </h3>
            <div className="space-y-2">
              {card?.linked_equipments?.map((eq: any) => (
                <div key={eq.id} className="flex items-center justify-between p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-md">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-blue-700 dark:text-blue-300">{eq.serial_number}</span>
                    <span className="text-xs text-slate-500">{eq.model}</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-slate-400 hover:text-red-500">
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
              <Select onValueChange={(v) => linkEquipment(parseInt(v))}>
                <SelectTrigger className="h-8 text-xs bg-white dark:bg-slate-900">
                  <SelectValue placeholder="Link equipment by S/N..." />
                </SelectTrigger>
                <SelectContent>
                  {availableEquipment.map(eq => (
                    <SelectItem key={eq.id} value={eq.id.toString()}>{eq.serial_number} - {eq.model}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Linked Tags */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <MapPin className="h-4 w-4 text-emerald-500" />
              Linked Instrument Tags
            </h3>
            <div className="space-y-2">
              {card?.linked_tags?.map((tag: any) => (
                <div key={tag.id} className="flex items-center justify-between p-2 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-100 dark:border-emerald-800 rounded-md">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-emerald-700 dark:text-emerald-300">{tag.tag_number}</span>
                    <span className="text-xs text-slate-500">{tag.description}</span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-slate-400 hover:text-red-500">
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
              <Select onValueChange={(v) => linkTag(parseInt(v))}>
                <SelectTrigger className="h-8 text-xs bg-white dark:bg-slate-900">
                  <SelectValue placeholder="Link tag (P&ID address)..." />
                </SelectTrigger>
                <SelectContent>
                  {availableTags.map(tag => (
                    <SelectItem key={tag.id} value={tag.id.toString()}>{tag.tag_number} - {tag.description}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Connected Cards */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <LinkIcon className="h-4 w-4 text-purple-500" />
              Connected Cards
            </h3>
            <div className="space-y-2">
              {card?.connections?.map((conn: any) => (
                <div key={conn.id} className="flex items-center justify-between p-2 bg-purple-50 dark:bg-purple-900/20 border border-purple-100 dark:border-purple-800 rounded-md">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-purple-700 dark:text-purple-300">#{conn.id}</span>
                    <span className="text-xs text-slate-500 line-clamp-1">{conn.title}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-slate-400 hover:text-red-500"
                    onClick={() => unlinkCard(conn.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
              <Select onValueChange={(v) => linkCard(parseInt(v))}>
                <SelectTrigger className="h-8 text-xs bg-white dark:bg-slate-900">
                  <SelectValue placeholder="Link related card..." />
                </SelectTrigger>
                <SelectContent>
                  {availableCards
                    .filter(c => c.id !== card?.id)
                    .map(c => (
                      <SelectItem key={c.id} value={c.id.toString()}>#{c.id} - {c.title}</SelectItem>
                    ))
                  }
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Comments Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Comments ({card?.comments?.length || 0})
            </h3>

            <div className="space-y-4">
              {card?.comments?.map((c: any) => (
                <div key={c.id} className="flex gap-3">
                  <div className="h-9 w-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-[10px] font-bold text-white shadow-sm ring-2 ring-white dark:ring-slate-900 overflow-hidden">
                    {c.author.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold">{c.author}</span>
                      <span className="text-slate-400">{new Date(c.created_at).toLocaleString()}</span>
                    </div>
                    <div className="bg-slate-100 dark:bg-slate-800 p-2 rounded-lg text-sm">
                      {c.text}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-2 pt-2">
              <Textarea
                placeholder="Write a comment..."
                className="text-sm min-h-[80px]"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
              <div className="flex justify-end">
                <Button size="sm" className="gap-2" onClick={addComment}>
                  <Save className="h-3.5 w-3.5" />
                  Post Comment
                </Button>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
