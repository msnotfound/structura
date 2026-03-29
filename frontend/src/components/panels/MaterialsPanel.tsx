import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import type { MaterialsResult, MaterialRecommendation } from '@/types'
import { Package, DollarSign, Star, Leaf } from 'lucide-react'

interface MaterialsPanelProps {
  result: MaterialsResult
}

export function MaterialsPanel({ result }: MaterialsPanelProps) {
  const recommendations = result.recommendations ?? []
  // API returns total_material_cost, fallback to total_estimated_cost
  const totalCost = (result as any).total_material_cost ?? result.total_estimated_cost ?? 0
  const costBreakdown = result.cost_breakdown ?? []

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
              ₹{totalCost.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Cost Breakdown */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-3">Cost Breakdown</h4>
          <div className="space-y-2">
            {costBreakdown.map((item: any) => (
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
            {recommendations.slice(0, 4).map((rec: any, idx: number) => (
              <MaterialCard key={rec.element_id ?? idx} recommendation={rec} />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function MaterialCard({ recommendation }: { recommendation: any }) {
  // API returns options[] not recommended_materials[]
  const options = recommendation.options ?? recommendation.recommended_materials ?? []
  const topOption = options[0]
  if (!topOption) return null

  const material = topOption.material ?? {}
  const score = topOption.score ?? topOption.suitability_score ?? 0
  const costEstimate = material.cost_per_unit ?? topOption.cost_estimate ?? 0

  return (
    <div className="p-3 border rounded-lg">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-sm font-medium">{recommendation.element_type}</p>
          <p className="text-xs text-muted-foreground">{recommendation.element_description ?? recommendation.element_id}</p>
        </div>
        <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full font-medium">{(score * 100).toFixed(0)}% match</span>
      </div>
      
      <div className="flex items-center gap-4 mt-2">
        <div className="flex-1">
          <p className="text-sm font-medium text-primary">{material.name ?? 'Unknown'}</p>
          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
            <span>₹{costEstimate.toLocaleString()}/{material.unit ?? 'unit'}</span>
            <span>Durability: {material.durability_rating ?? '—'}/10</span>
            <span>Eco: {material.environmental_score ?? '—'}/10</span>
          </div>
        </div>
      </div>
      {topOption.meets_requirements === false && (
        <p className="text-xs text-red-500 mt-1">{topOption.disqualification_reason}</p>
      )}
    </div>
  )
}
