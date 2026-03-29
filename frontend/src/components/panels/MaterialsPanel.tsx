import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import type { MaterialsResult, MaterialRecommendation } from '@/types'
import { Package, DollarSign, Star, Leaf } from 'lucide-react'

interface MaterialsPanelProps {
  result: MaterialsResult
}

export function MaterialsPanel({ result }: MaterialsPanelProps) {
  const { recommendations, total_estimated_cost, cost_breakdown } = result

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="w-5 h-5" />
          Material Recommendations
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Total Cost */}
        <div className="p-4 bg-primary/10 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Estimated Total</span>
            <span className="text-2xl font-bold text-primary">
              ₹{total_estimated_cost.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Cost Breakdown */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-3">Cost Breakdown</h4>
          <div className="space-y-2">
            {cost_breakdown.map(item => (
              <div key={item.category} className="flex items-center justify-between">
                <span className="text-sm">{item.category}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">₹{item.cost.toLocaleString()}</span>
                  <Badge variant="default">{item.percentage.toFixed(0)}%</Badge>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Recommendations */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-3">Top Recommendations</h4>
          <div className="space-y-3">
            {recommendations.slice(0, 4).map(rec => (
              <MaterialCard key={rec.element_id} recommendation={rec} />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function MaterialCard({ recommendation }: { recommendation: MaterialRecommendation }) {
  const topMaterial = recommendation.recommended_materials[0]
  if (!topMaterial) return null

  const { material, suitability_score, cost_estimate } = topMaterial

  return (
    <div className="p-3 border rounded-lg">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-sm font-medium">{recommendation.element_type}</p>
          <p className="text-xs text-muted-foreground">{recommendation.element_id}</p>
        </div>
        <Badge variant="success">{(suitability_score * 100).toFixed(0)}% match</Badge>
      </div>
      
      <div className="flex items-center gap-4 mt-2">
        <div className="flex-1">
          <p className="text-sm font-medium text-primary">{material.name}</p>
          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              ₹{cost_estimate.toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
              <Star className="w-3 h-3" />
              {material.durability_rating}/10
            </span>
            <span className="flex items-center gap-1">
              <Leaf className="w-3 h-3" />
              {material.environmental_score}/10
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
