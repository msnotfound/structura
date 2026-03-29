import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import type { ProjectCost } from '@/types'
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip,
  Legend 
} from 'recharts'
import { Calculator, TrendingUp, Home } from 'lucide-react'

interface CostPanelProps {
  cost: ProjectCost
}

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']

export function CostPanel({ cost }: CostPanelProps) {
  const api = cost as any
  const grand_total = api.grand_total ?? 0
  const currency = api.currency ?? '₹'
  // API has cost_per_sqm not cost_per_sqft
  const cost_per_unit = api.cost_per_sqm ?? api.cost_per_sqft ?? 0
  const unit_label = api.cost_per_sqm !== undefined ? 'per sq.m' : 'per sq.ft'
  // API has category_totals not category_costs  
  const category_costs: any[] = api.category_totals ?? api.category_costs ?? []
  // API has line_items not room_costs
  const room_costs: any[] = api.room_totals ?? api.room_costs ?? []

  // Prepare pie chart data
  const pieData = category_costs.map(cat => ({
    name: cat.category,
    value: cat.subtotal ?? cat.total ?? 0,
  }))

  // Prepare bar chart data for rooms
  const barData = room_costs.slice(0, 6).map(room => ({
    name: room.room_name ?? room.category ?? 'Room',
    cost: room.subtotal ?? room.total ?? 0,
    area: room.area ?? 0,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="w-5 h-5" />
          Cost Estimation
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Grand Total */}
        <div className="p-4 bg-gradient-to-r from-primary/10 to-accent/10 rounded-lg">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Grand Total</p>
            <p className="text-3xl font-bold text-foreground">
              {currency} {grand_total.toLocaleString()}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              {currency} {cost_per_unit.toFixed(0)} {unit_label}
            </p>
          </div>
        </div>

        {/* Cost Breakdown */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-muted-foreground">Budget</p>
            <p className="text-sm font-medium">{currency} {(api.budget_total ?? 0).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Premium</p>
            <p className="text-sm font-medium">{currency} {(api.premium_total ?? 0).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Savings vs Premium</p>
            <p className="text-sm font-medium">{currency} {(api.savings_vs_premium ?? 0).toLocaleString()}</p>
          </div>
        </div>

        {/* Category Pie Chart */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">By Category</h4>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: any) => [`${currency} ${Number(value).toLocaleString()}`, 'Cost']}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Room Costs Bar Chart */}
        {barData.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-2">By Room</h4>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} layout="vertical">
                  <XAxis type="number" tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
                  <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value: any) => [`${currency} ${Number(value).toLocaleString()}`, 'Cost']}
                  />
                  <Bar dataKey="cost" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Category Details */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">Category Details</h4>
          <div className="space-y-2">
            {category_costs.map((cat, idx) => (
              <div key={cat.category} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                  />
                  <span>{cat.category}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{currency} {cat.subtotal.toLocaleString()}</span>
                  <span className="text-muted-foreground">({cat.percentage_of_total.toFixed(1)}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
