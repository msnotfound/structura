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

  return {
    result,
    stage,
    progress,
    error,
    analyze,
    reset,
  }
}
