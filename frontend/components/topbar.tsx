"use client"

import React from "react"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu"
import { Bell, ChevronDown, LayoutDashboard, Settings, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import Image from "next/image"
import { cn } from "@/lib/utils"

export function Topbar() {
  const [unreadCount, setUnreadCount] = React.useState(0)

  React.useEffect(() => {
    const fetchUnreadCount = async () => {
      try {
        const response = await fetch("/api/alerts?acknowledged=false")
        const data = await response.json()
        setUnreadCount(data.length)
      } catch (error) {
        console.error("Failed to fetch unread alerts", error)
      }
    }
    fetchUnreadCount()
    // Poll every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="h-16 border-b flex items-center justify-between px-6 bg-[#003D5C] text-white shadow-md z-30">
      <div className="flex items-center gap-8">
        {/* Brand / Logo Section */}
        <Link href="/dashboard" className="flex items-center gap-4 hover:opacity-80 transition-opacity">
          <div className="bg-white p-1 rounded-sm">
            <Image
              src="/sbm-logo.png"
              alt="SBM Offshore"
              width={100}
              height={32}
              className="object-contain h-8 w-auto"
            />
          </div>
          <div className="h-6 w-px bg-white/20" />
          <span className="font-bold tracking-tight text-lg underline-offset-4 decoration-[#FF6B35]">MMT</span>
        </Link>

        {/* Horizontal Navigation */}
        <NavigationMenu>
          <NavigationMenuList className="gap-2">

            {/* Core Modules Menu */}
            <NavigationMenuItem>
              <NavigationMenuTrigger className="text-white hover:text-white hover:bg-white/10">Core Modules</NavigationMenuTrigger>
              <NavigationMenuContent>
                <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px] bg-white border shadow-xl rounded-lg">
                  <ListItem href="/dashboard/equipment" title="Managing Equipment (M1)">
                    Manage physical assets and logical tags.
                  </ListItem>
                  <ListItem href="/dashboard/metrology" title="Metrological Confirmation (M2)">
                    Calibration campaigns and certificates.
                  </ListItem>
                  <ListItem href="/dashboard/chemical" title="Chemical Analysis (M3)">
                    Oil and gas sampling and laboratory analysis.
                  </ListItem>
                  <ListItem href="/dashboard/maintenance" title="Onshore Maintenance (M4)">
                    Kanban board for maintenance workflows.
                  </ListItem>
                  <ListItem href="/dashboard/planning" title="Planning (M8)">
                    Asset inventory and verification planning.
                  </ListItem>
                  <ListItem href="/dashboard/failure-notification" title="Failure Notification (M9)">
                    Register and track meter failures.
                  </ListItem>
                </ul>
              </NavigationMenuContent>
            </NavigationMenuItem>

            {/* Support & Tools Menu */}
            <NavigationMenuItem>
              <NavigationMenuTrigger className="text-white hover:text-white hover:bg-white/10">Support & Tools</NavigationMenuTrigger>
              <NavigationMenuContent>
                <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px] bg-white border shadow-xl rounded-lg">
                  <ListItem href="/dashboard/monitoring" title="Monitoring & Alerts (M6)">
                    Real-time thresholds and notifications.
                  </ListItem>
                  <ListItem href="/dashboard/sync" title="Synchronization Data (M5)">
                    HMI connections and data dumps.
                  </ListItem>
                  <ListItem href="/dashboard/export" title="Export Data (M7)">
                    Data extraction and XML reporting.
                  </ListItem>
                  <ListItem href="/dashboard/reports" title="Historical Report (M10)">
                    Archive of unit reports and documents.
                  </ListItem>
                </ul>
              </NavigationMenuContent>
            </NavigationMenuItem>

            {/* Admin Menu */}
            <NavigationMenuItem>
              <NavigationMenuLink asChild>
                <Link
                  href="/dashboard/configurations"
                  className={cn(
                    "group inline-flex h-10 w-max items-center justify-center rounded-md bg-transparent px-4 py-2 text-sm font-medium transition-colors hover:bg-white/10 hover:text-white focus:bg-white/10 focus:text-white focus:outline-none disabled:pointer-events-none disabled:opacity-50"
                  )}
                >
                  Configurations (M11)
                </Link>
              </NavigationMenuLink>
            </NavigationMenuItem>

          </NavigationMenuList>
        </NavigationMenu>
      </div>

      <div className="flex items-center gap-6">
        {/* Global FPSO Selector */}
        <div className="w-[200px]">
          <Select defaultValue="sepetiba">
            <SelectTrigger className="h-9 border-white/20 bg-white/10 text-white hover:bg-white/20 transition-colors">
              <SelectValue placeholder="Select FPSO" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="sepetiba">FPSO SEPETIBA</SelectItem>
              <SelectItem value="saquarema">FPSO SAQUAREMA</SelectItem>
              <SelectItem value="marica">FPSO MARICÁ</SelectItem>
              <SelectItem value="paraty">FPSO PARATY</SelectItem>
              <SelectItem value="ilhabela">FPSO ILHABELA</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/dashboard/monitoring">
            <Button variant="ghost" size="icon" className="h-9 w-9 text-white hover:bg-white/10 relative">
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-[#FF6B35] rounded-full border border-[#003D5C] text-[10px] flex items-center justify-center font-bold">
                  {unreadCount}
                </span>
              )}
            </Button>
          </Link>

          <div className="h-8 w-px bg-white/20 ml-2" />
        </div>
      </div>
    </header>
  )
}

const ListItem = React.forwardRef<
  HTMLAnchorElement,
  React.ComponentPropsWithoutRef<typeof Link> & { title: string }
>(({ className, title, children, ...props }, ref) => {
  return (
    <li>
      <NavigationMenuLink asChild>
        <Link
          ref={ref}
          className={cn(
            "block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-slate-50 hover:text-black focus:bg-slate-50 focus:text-black",
            className
          )}
          {...props}
        >
          <div className="text-sm font-bold leading-none text-[#003D5C]">{title}</div>
          <p className="line-clamp-2 text-xs leading-snug text-slate-500 font-medium">
            {children}
          </p>
        </Link>
      </NavigationMenuLink>
    </li>
  )
})
ListItem.displayName = "ListItem"
