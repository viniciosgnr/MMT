"use client"

import { useState, useEffect } from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { apiFetch } from "@/lib/api"
import { CardDetails } from "./card-details"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { format } from "date-fns"
import { MoreHorizontal } from "lucide-react"

interface ListViewProps {
  search: string
  fpsoFilter: string | null
}

export function MaintenanceListView({ search, fpsoFilter }: ListViewProps) {
  const [columns, setColumns] = useState<any[]>([])
  const [cards, setCards] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [colsRes, cardsRes] = await Promise.all([
        apiFetch(`/maintenance/columns`),
        apiFetch(`/maintenance/cards?search=${search}${fpsoFilter ? `&fpso=${fpsoFilter}` : ""}`)
      ])

      if (colsRes.ok && cardsRes.ok) {
        const colsData = await colsRes.json()
        const cardsData = await cardsRes.json()
        setColumns(colsData || [])
        setCards(cardsData || [])
      }
    } catch (error) {
      console.error("Failed to fetch list data", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [search, fpsoFilter])

  const getStatusName = (colId: number) => {
    const col = columns.find(c => c.id === colId)
    return col ? col?.name : "Unknown"
  }

  const getStatusClassName = (statusName: string) => {
    switch (statusName?.toLowerCase()) {
      case "backlog": return "bg-slate-100 text-slate-700 border-slate-200"
      case "in progress": return "bg-blue-100 text-blue-700 border-blue-200"
      case "review": return "bg-amber-100 text-amber-700 border-amber-200"
      case "done": return "bg-emerald-100 text-emerald-700 border-emerald-200"
      case "blocked": return "bg-red-100 text-red-700 border-red-200"
      default: return "bg-slate-100 text-slate-700 border-slate-200"
    }
  }

  const getFPSOColor = (fpsoName: string) => {
    if (!fpsoName) return "bg-slate-50 text-slate-600 border-slate-200"

    const name = fpsoName.toUpperCase()
    if (name.includes("PARATY")) return "bg-indigo-50 text-indigo-700 border-indigo-200"
    if (name.includes("ILHABELA")) return "bg-violet-50 text-violet-700 border-violet-200"
    if (name.includes("MARICÁ") || name.includes("MARICA")) return "bg-purple-50 text-purple-700 border-purple-200"
    if (name.includes("SAQUAREMA")) return "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200"
    if (name.includes("SEPETIBA")) return "bg-pink-50 text-pink-700 border-pink-200"

    return "bg-slate-50 text-slate-600 border-slate-200"
  }

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading tasks...</div>
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg border shadow-sm mx-6 my-6 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-50">
            <TableHead className="w-[80px]">ID</TableHead>
            <TableHead>Title</TableHead>
            <TableHead>FPSO</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Responsible</TableHead>
            <TableHead>Due Date</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {cards.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                No tasks found.
              </TableCell>
            </TableRow>
          ) : (
            cards.map((card) => {
              const statusName = getStatusName(card.column_id)
              return (
                <TableRow
                  key={card.id}
                  className="cursor-pointer hover:bg-slate-50/80 transition-colors"
                  onClick={() => {
                    setSelectedCardId(card.id)
                    setDetailsOpen(true)
                  }}
                >
                  <TableCell className="font-medium text-slate-500">#{card.id}</TableCell>
                  <TableCell>
                    <div className="font-semibold text-slate-900 dark:text-slate-100">{card.title}</div>
                    <div className="text-xs text-slate-500 truncate max-w-[300px]">{card.description}</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`text-[10px] font-bold tracking-wider ${getFPSOColor(card.fpso)}`}>
                      {card.fpso || "N/A"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`font-medium border ${getStatusClassName(statusName)}`}>
                      {statusName}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {card.responsible ? (
                        <>
                          <Avatar className="h-6 w-6 border-2 border-white shadow-sm">
                            <AvatarFallback className="text-[10px] bg-gradient-to-br from-blue-500 to-blue-600 text-white font-bold">
                              {card.responsible.substring(0, 2).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-sm font-medium text-slate-700">{card.responsible}</span>
                        </>
                      ) : (
                        <span className="text-sm text-slate-400 italic">Unassigned</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-slate-600">
                    {card.due_date ? format(new Date(card.due_date), "MMM d, yyyy") : "-"}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })
          )}
        </TableBody>
      </Table>

      <CardDetails
        cardId={selectedCardId}
        open={detailsOpen}
        onOpenChange={(open) => {
          setDetailsOpen(open)
          if (!open) {
            setSelectedCardId(null)
            fetchData() // Refresh list on close
          }
        }}
        onUpdated={fetchData}
      />
    </div>
  )
}
