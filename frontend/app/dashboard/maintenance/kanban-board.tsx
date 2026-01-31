"use client"

import { useState, useEffect } from "react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Calendar,
  User,
  Tag,
  Paperclip,
  MessageSquare,
  MoreVertical,
  ChevronRight,
  ArrowRightLeft,
  Plus
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { CardDetails } from "./card-details"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

interface KanbanBoardProps {
  search: string
  fpsoFilter: string | null
  onAddNew?: (columnId: number) => void
}

export function KanbanBoard({ search, fpsoFilter, onAddNew }: KanbanBoardProps) {
  const [columns, setColumns] = useState<any[]>([])
  const [cards, setCards] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [colsRes, cardsRes] = await Promise.all([
        fetch(`${API_URL}/maintenance/columns`),
        fetch(`${API_URL}/maintenance/cards?search=${search}${fpsoFilter ? `&fpso=${fpsoFilter}` : ""}`)
      ])

      const colsData = await colsRes.json()
      const cardsData = await cardsRes.json()

      if (Array.isArray(colsData)) setColumns(colsData)
      else setColumns([])

      if (Array.isArray(cardsData)) setCards(cardsData)
      else setCards([])
    } catch (error) {
      console.error("Failed to fetch Kanban data", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [search, fpsoFilter])

  const moveCard = async (cardId: number, newColumnId: number) => {
    try {
      const res = await fetch(`${API_URL}/maintenance/cards/${cardId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ column_id: newColumnId })
      })
      if (res.ok) fetchData()
    } catch (error) {
      console.error("Failed to move card", error)
    }
  }

  const handleCardClick = (cardId: number) => {
    setSelectedCardId(cardId)
    setDetailsOpen(true)
  }

  if (loading && columns.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 bg-slate-50/30">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
          <span className="text-sm font-medium tracking-wide">Loading MMT Kanban...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full overflow-x-auto pb-4 gap-0 items-start select-none bg-slate-50/50 dark:bg-slate-950/50 custom-scrollbar">
      {columns.map(col => (
        <div
          key={col.id}
          className="flex-shrink-0 w-80 h-full flex flex-col border-r border-slate-200/60 dark:border-slate-800/60 last:border-r-0"
        >
          {/* Column Header - Compact & Sticky */}
          <div className="flex items-center justify-between px-4 py-3 bg-white/40 dark:bg-slate-900/40 backdrop-blur-sm sticky top-0 z-20 border-b border-slate-200/40">
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
              <h3 className="font-bold text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-[0.15em]">
                {col.name}
              </h3>
              <span className="inline-flex items-center justify-center px-1.5 py-0.5 rounded-md bg-slate-200/50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 text-[10px] font-bold">
                {cards.filter(c => c.column_id === col.id).length}
              </span>
            </div>
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0 hover:bg-slate-200/50 dark:hover:bg-slate-800/50">
              <MoreVertical className="h-3.5 w-3.5 text-slate-400" />
            </Button>
          </div>

          {/* Cards Container - Dedicated Lane */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-slate-100/30 dark:bg-slate-900/20 custom-scrollbar">
            {cards
              .filter(card => card.column_id === col.id)
              .map(card => (
                <Card
                  key={card.id}
                  className="group relative cursor-pointer hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] transition-all duration-300 border border-slate-200 dark:border-slate-800 hover:border-blue-400/50 dark:hover:border-blue-700 bg-white dark:bg-slate-900 overflow-hidden rounded-xl shadow-[0_2px_10px_rgb(0,0,0,0.02)]"
                  onClick={() => handleCardClick(card.id)}
                >
                  {/* Priority Indicator Line */}
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500/20 to-transparent" />

                  <CardContent className="p-4 space-y-4">
                    {/* Tags / Labels */}
                    <div className="flex flex-wrap gap-1.5">
                      {card.labels?.map((label: any) => (
                        <div
                          key={label.id}
                          className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-tight shadow-sm"
                          style={{
                            backgroundColor: `${label.color}15`,
                            color: label.color,
                            border: `1px solid ${label.color}30`
                          }}
                        >
                          {label.name}
                        </div>
                      ))}
                    </div>

                    <div className="space-y-1">
                      <h4 className="font-medium text-sm leading-tight group-hover:text-blue-600 transition-colors">
                        {card.title}
                      </h4>
                      <p className="text-[12px] text-slate-500 line-clamp-2">
                        {card.description}
                      </p>
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 text-slate-400">
                        {card.comments?.length > 0 && (
                          <div className="flex items-center gap-1">
                            <MessageSquare className="h-3 w-3" />
                            <span className="text-[10px]">{card.comments.length}</span>
                          </div>
                        )}
                        {card.attachments?.length > 0 && (
                          <div className="flex items-center gap-1">
                            <Paperclip className="h-3 w-3" />
                            <span className="text-[10px]">{card.attachments.length}</span>
                          </div>
                        )}
                        {(card.linked_equipments?.length > 0 || card.linked_tags?.length > 0) && (
                          <div className="flex items-center gap-1 text-blue-500/80">
                            <ArrowRightLeft className="h-3 w-3" />
                            <span className="text-[10px] font-bold">
                              {(card.linked_equipments?.length || 0) + (card.linked_tags?.length || 0)}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 text-slate-500 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-[10px]">
                        <Calendar className="h-3 w-3" />
                        <span>{card.due_date ? new Date(card.due_date).toLocaleDateString() : "--/--"}</span>
                      </div>
                    </div>
                  </CardContent>

                  {/* Quick Actions (Hover) */}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm shadow-sm border border-slate-200 dark:border-slate-700">
                          <MoreVertical className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem disabled>Move to...</DropdownMenuItem>
                        {columns.filter(c => c.id !== col.id).map(targetCol => (
                          <DropdownMenuItem key={targetCol.id} onClick={() => moveCard(card.id, targetCol.id)}>
                            <ChevronRight className="h-3 w-3 mr-2 opacity-50" />
                            {targetCol.name}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </Card>
              ))}

            {/* Add Card Placeholder */}
            <button
              className="w-full py-3 border border-dashed border-slate-300 dark:border-slate-700 rounded-xl flex items-center justify-center gap-2 text-slate-400 hover:text-blue-500 hover:border-blue-400 hover:bg-blue-50/30 dark:hover:bg-blue-900/10 transition-all group"
              onClick={() => onAddNew?.(col.id)}
            >
              <Plus className="h-4 w-4 transform group-hover:scale-110 transition-transform" />
              <span className="text-[10px] font-bold uppercase tracking-wider">Add task</span>
            </button>
          </div>
        </div>
      ))}

      {/* Card Details Modal */}
      {selectedCardId && (
        <CardDetails
          cardId={selectedCardId}
          open={detailsOpen}
          onOpenChange={setDetailsOpen}
          onUpdated={fetchData}
        />
      )}

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
        }
        .dark .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #334155;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </div>
  )
}
