import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import type { FullReport } from '@/types'
import { FileText, Lightbulb, AlertTriangle, CheckCircle } from 'lucide-react'

interface ReportPanelProps {
  report: FullReport
}

export function ReportPanel({ report }: ReportPanelProps) {
  const api = report as any
  // API uses project_summary, overall_assessment; frontend type has summary, structural_assessment
  const summary = api.project_summary ?? api.summary ?? ''
  const structural_assessment = api.overall_assessment ?? api.structural_assessment ?? ''
  const optimization_suggestions: any[] = api.optimization_suggestions ?? []
  const warnings_summary = api.cost_summary ?? api.warnings_summary ?? null
  // No recommendations array in API, show limitations instead
  const recommendations: string[] = api.limitations ?? api.recommendations ?? []


  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Analysis Report
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">Summary</h4>
          <p className="text-sm leading-relaxed">{summary}</p>
        </div>

        {/* Structural Assessment */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">Structural Assessment</h4>
          <p className="text-sm leading-relaxed">{structural_assessment}</p>
        </div>

        {/* Warnings Summary */}
        {warnings_summary && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800">Warnings</h4>
                <p className="text-sm text-yellow-700 mt-1">{warnings_summary}</p>
              </div>
            </div>
          </div>
        )}

        {/* Optimization Suggestions */}
        {optimization_suggestions.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              Optimization Suggestions
            </h4>
            <div className="space-y-3">
              {optimization_suggestions.map((suggestion: any) => (
                <div key={suggestion.id} className="p-3 border rounded-lg">
                  <div className="flex items-start justify-between mb-1">
                    <h5 className="text-sm font-medium">{suggestion.title}</h5>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      (suggestion.priority ?? suggestion.impact_level) === 'high' ? 'bg-green-100 text-green-800' :
                      (suggestion.priority ?? suggestion.impact_level) === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {suggestion.priority ?? suggestion.impact_level ?? 'low'}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">{suggestion.description}</p>
                  {suggestion.potential_savings && (
                    <p className="text-sm text-green-600 mt-2">
                      Potential savings: ₹{Number(suggestion.potential_savings).toLocaleString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Recommendations
            </h4>
            <ul className="space-y-2">
              {recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm">
                  <span className="text-primary">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
