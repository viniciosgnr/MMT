"use client"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Bell, AlertTriangle, Check, Settings, Plus } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

// Mock Alerts
const alerts = [
  { id: 1, severity: "Critical", message: "Flow Rate Deviation > 5%", tag: "T62-FT-1103", time: "10 mins ago", status: "Active" },
  { id: 2, severity: "Warning", message: "Calibration Due in 7 Days", tag: "T62-PT-1103", time: "2 hours ago", status: "Active" },
  { id: 3, severity: "Info", message: "System Backup Completed", tag: "System", time: "1 day ago", status: "Acknowledged" },
]

// Mock Rules
const rules = [
  { id: 1, name: "Flow Deviation", condition: "Value > 5% of Setpoint", priority: "Critical" },
  { id: 2, name: "Pressure High", condition: "Value > 100 bar", priority: "Warning" },
]

export default function MonitoringAlertsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Monitoring & Alerts (M6)</h1>
          <p className="text-muted-foreground">Manage real-time alerts and monitoring thresholds.</p>
        </div>
      </div>

      <Tabs defaultValue="active" className="w-full">
        <TabsList>
          <TabsTrigger value="active">Active Alerts</TabsTrigger>
          <TabsTrigger value="rules">Alert Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4 mt-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Critical Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">1</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Warnings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-yellow-600">1</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Live Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Severity</TableHead>
                    <TableHead>Message</TableHead>
                    <TableHead>Tag/Source</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell>
                        {alert.severity === 'Critical' && <Badge variant="destructive">Critical</Badge>}
                        {alert.severity === 'Warning' && <Badge className="bg-yellow-500 hover:bg-yellow-600">Warning</Badge>}
                        {alert.severity === 'Info' && <Badge variant="secondary">Info</Badge>}
                      </TableCell>
                      <TableCell className="font-medium">{alert.message}</TableCell>
                      <TableCell>{alert.tag}</TableCell>
                      <TableCell className="text-muted-foreground">{alert.time}</TableCell>
                      <TableCell>{alert.status}</TableCell>
                      <TableCell className="text-right">
                        {alert.status === 'Active' && (
                          <Button size="sm" variant="ghost">
                            <Check className="mr-2 h-4 w-4" /> Acknowledge
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rules" className="mt-4">
          <div className="flex justify-end mb-4">
            <Button>
              <Plus className="mr-2 h-4 w-4" /> Add New Rule
            </Button>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Configuration Rules</CardTitle>
              <CardDescription>Define thresholds and conditions for alerts.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rule Name</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Default Priority</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell className="font-medium">{rule.name}</TableCell>
                      <TableCell>{rule.condition}</TableCell>
                      <TableCell>{rule.priority}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon"><Settings className="h-4 w-4" /></Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
