import { useState, useCallback } from 'react'
import type { AnalysisResult } from '@/types'
import { uploadAndAnalyze } from '@/api/client'

type AnalysisStage = 
  | 'idle' 
  | 'uploading' 
  | 'parsing' 
  | 'analyzing' 
  | 'generating' 
  | 'complete' 
  | 'error'

interface UseAnalysisReturn {
  result: AnalysisResult | null
  stage: AnalysisStage
  progress: string
  error: string | null
  analyze: (file: File) => Promise<void>
  reset: () => void
  loadFromData: (data: any) => void
}

export function useAnalysis(): UseAnalysisReturn {
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [stage, setStage] = useState<AnalysisStage>('idle')
  const [progress, setProgress] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const analyze = useCallback(async (file: File) => {
    setStage('uploading')
    setError(null)
    setProgress('Uploading floor plan...')

    try {
      const analysisResult = await uploadAndAnalyze(file, (msg) => {
        setProgress(msg)
        if (msg.includes('Analyzing')) {
          setStage('analyzing')
        }
      })
      
      setResult(analysisResult)
      setStage('complete')
      setProgress('Analysis complete!')
    } catch (err) {
      console.error('Analysis error:', err)
      setError(err instanceof Error ? err.message : 'Analysis failed')
      setStage('error')
    }
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setStage('idle')
    setProgress('')
    setError(null)
  }, [])

  const loadFromData = useCallback((data: any) => {
    // Load analysis from saved history data
    const loaded: AnalysisResult = {
      file_id: data.file_id ?? '',
      parse_result: data.parse_result,
      geometry_result: data.geometry_result,
      structural_result: data.structural_result,
      materials_result: data.materials_result,
      cost_result: data.cost_result,
      report: data.report,
      scene_graph: data.scene_graph,
    }
    setResult(loaded)
    setStage('complete')
    setProgress('Loaded from history')
    setError(null)
  }, [])

  return {
    result,
    stage,
    progress,
    error,
    analyze,
    reset,
    loadFromData,
  }
}
