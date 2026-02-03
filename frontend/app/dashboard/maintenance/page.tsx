"use client"

import { useState, useEffect } from "react"
import { KanbanBoard } from "./kanban-board"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Plus,
  Search,
  Filter,
  LayoutGrid,
  List as ListIcon,
  MoreHorizontal,
  ChevronDown
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { NewCardDialog } from "./new-card-dialog"
import { MaintenanceListView } from "./list-view"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export default function MaintenancePage() {
  const [view, setView] = useState<"kanban" | "list">("kanban")
  const [search, setSearch] = useState("")
  const [fpsoFilter, setFpsoFilter] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [newCardOpen, setNewCardOpen] = useState(false)
  const [selectedColId, setSelectedColId] = useState<number | null>(null)

  const handleRefresh = () => setRefreshKey(prev => prev + 1)
  const handleAddNew = (colId: number) => {
    setSelectedColId(colId)
    setNewCardOpen(true)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-slate-50/50 dark:bg-slate-950/50">
      {/* Upper Header / Toolbar */}
      {/* Upper Header / Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 sm:p-6 border-b bg-white dark:bg-slate-900 shadow-sm z-10 gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-1 bg-blue-600 rounded-full hidden sm:block" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Onshore Maintenance (M4)</h1>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge variant="outline" className="bg-blue-50/50 text-blue-700 border-blue-200/50 dark:bg-blue-900/10 dark:text-blue-400 dark:border-blue-800/50 text-[10px] font-medium uppercase tracking-wider">
                Kanban Workspace
              </Badge>
              <div className="h-1 w-1 rounded-full bg-slate-300 dark:bg-slate-700" />
              <span className="text-xs text-slate-500">Manage assets in repair/calibration</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
            <Input
              placeholder="Search tasks, serials..."
              className="pl-10 h-10 bg-slate-50/50 border-slate-200 focus-visible:ring-blue-500 transition-all rounded-lg"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="h-10 gap-2 border-slate-200 rounded-lg">
                  <Filter className="h-4 w-4 text-slate-500" />
                  <span className="hidden lg:inline">{fpsoFilter || "All FPSOs"}</span>
                  <ChevronDown className="h-3 w-3 opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem onClick={() => setFpsoFilter(null)}>All FPSOs</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setFpsoFilter("FPSO SEPETIBA")}>FPSO SEPETIBA</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setFpsoFilter("FPSO SAQUAREMA")}>FPSO SAQUAREMA</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setFpsoFilter("FPSO MARICÁ")}>FPSO MARICÁ</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setFpsoFilter("FPSO PARATY")}>FPSO PARATY</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setFpsoFilter("FPSO ILHABELA")}>FPSO ILHABELA</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <div className="flex h-10 border rounded-lg p-1 bg-slate-100/80 dark:bg-slate-800/50 border-slate-200 dark:border-slate-800">
              <Button
                variant={view === "kanban" ? "secondary" : "ghost"}
                size="sm"
                className={cn(
                  "h-full w-9 p-0 rounded-md transition-all",
                  view === "kanban" && "bg-white dark:bg-slate-700 shadow-sm"
                )}
                onClick={() => setView("kanban")}
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant={view === "list" ? "secondary" : "ghost"}
                size="sm"
                className={cn(
                  "h-full w-9 p-0 rounded-md transition-all",
                  view === "list" && "bg-white dark:bg-slate-700 shadow-sm"
                )}
                onClick={() => setView("list")}
              >
                <ListIcon className="h-4 w-4" />
              </Button>
            </div>

            <Button
              className="h-10 gap-2 bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-500/10 transition-all rounded-lg px-4"
              onClick={() => setNewCardOpen(true)}
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">New Card</span>
            </Button>
          </div>
        </div>
      </div>

      <NewCardDialog
        open={newCardOpen}
        onOpenChange={(open) => {
          setNewCardOpen(open)
          if (!open) setSelectedColId(null)
        }}
        onCreated={handleRefresh}
        initialColumnId={selectedColId}
      />

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {view === "kanban" ? (
          <KanbanBoard
            key={refreshKey}
            search={search}
            fpsoFilter={fpsoFilter}
            onAddNew={handleAddNew}
          />
        ) : (
          <MaintenanceListView
            search={search}
            fpsoFilter={fpsoFilter}
          />
        )}
      </div>
    </div>
  )
}
