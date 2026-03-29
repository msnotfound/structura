import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { SeverityBadge } from '@/components/ui/Badge'
import { ScoreBar } from '@/components/ui/Progress'
import type { StructuralAnalysisResult } from '@/types'
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

interface StructuralPanelProps {
  result: StructuralAnalysisResult
}

export function StructuralPanel({ result }: StructuralPanelProps) {
  const { 
    span_analyses = [], 
    warnings = [], 
  } = result
  
  const score = result.overall_structural_score ?? result.overall_integrity_score ?? 0
  const load_path_valid = result.load_path_valid
  const thickness_adequate = result.thickness_adequate

  const criticalWarnings = warnings.filter(w => w.severity === 'critical')
  const otherWarnings = warnings.filter(w => w.severity !== 'critical')


  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Structural Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Score */}
        <div>
          <ScoreBar
            score={score}
            label="Structural Integrity"
            color={score > 0.7 ? 'green' : score > 0.4 ? 'yellow' : 'red'}
          />
        </div>

        {/* Quick Status */}
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2">
            {load_path_valid ? (
              <CheckCircle className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-red-500" />
            )}
            <span className="text-sm">Load Path</span>
          </div>
          <div className="flex items-center gap-2">
            {thickness_adequate ? (
              <CheckCircle className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-red-500" />
            )}
            <span className="text-sm">Wall Thickness</span>
          </div>
        </div>

        {/* Critical Warnings */}
        {criticalWarnings.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-red-600">Critical Issues</h4>
            {criticalWarnings.map(warning => (
              <div key={warning.id} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <SeverityBadge severity={warning.severity} />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-800">{warning.message}</p>
                    <p className="text-xs text-red-600 mt-1">{warning.recommendation}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Other Warnings */}
        {otherWarnings.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Warnings</h4>
            {otherWarnings.map(warning => (
              <div key={warning.id} className="p-3 bg-muted rounded-lg">
                <div className="flex items-start gap-2">
                  <SeverityBadge severity={warning.severity} />
                  <div className="flex-1">
                    <p className="text-sm">{warning.message}</p>
                    <p className="text-xs text-muted-foreground mt-1">{warning.recommendation}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Span Analysis Summary */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">Span Analysis</h4>
          <div className="space-y-1">
            {span_analyses.slice(0, 5).map(span => (
              <div key={span.room_id || span.room_label} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground truncate">{span.room_label}</span>
                <div className="flex items-center gap-2">
                  <span>{(span.max_span_m ?? 0).toFixed(1)}m</span>
                  {!span.requires_intermediate_support ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                </div>
              </div>
            ))}
            {span_analyses.length > 5 && (
              <p className="text-xs text-muted-foreground">
                +{span_analyses.length - 5} more walls
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
