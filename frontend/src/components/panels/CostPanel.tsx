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
  const { 
    category_costs, 
    room_costs,
    subtotal, 
    contingency_amount, 
    tax_amount, 
    grand_total,
    cost_per_sqft,
    currency 
  } = cost

  // Prepare pie chart data
  const pieData = category_costs.map(cat => ({
    name: cat.category,
    value: cat.subtotal,
  }))

  // Prepare bar chart data for rooms
  const barData = room_costs.slice(0, 6).map(room => ({
    name: room.room_name,
    cost: room.subtotal,
    area: room.area,
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
              {currency} {cost_per_sqft.toFixed(0)} per sq.ft
            </p>
          </div>
        </div>

        {/* Cost Breakdown */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-muted-foreground">Subtotal</p>
            <p className="text-sm font-medium">{currency} {subtotal.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Contingency</p>
            <p className="text-sm font-medium">{currency} {contingency_amount.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Tax</p>
            <p className="text-sm font-medium">{currency} {tax_amount.toLocaleString()}</p>
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
                  formatter={(value: number) => [`${currency} ${value.toLocaleString()}`, 'Cost']}
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
                    formatter={(value: number) => [`${currency} ${value.toLocaleString()}`, 'Cost']}
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
