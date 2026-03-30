import axios from 'axios'
import type {
  UploadResponse,
  AnalysisResult,
  Material,
  SceneGraph,
  FullReport,
  HealthResponse,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3 minutes for analysis
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function checkHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>('/health')
  return response.data
}

export async function uploadFloorPlan(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export async function analyzeFloorPlan(fileId: string): Promise<AnalysisResult> {
  const response = await api.post<AnalysisResult>(`/analyze/${fileId}`)
  return response.data
}

export async function getMaterials(): Promise<Material[]> {
  const response = await api.get<Material[]>('/materials')
  return response.data
}

export async function getSceneGraph(fileId: string): Promise<SceneGraph> {
  const response = await api.get<SceneGraph>(`/scene/${fileId}`)
  return response.data
}

export async function getReport(fileId: string): Promise<FullReport> {
  const response = await api.get<FullReport>(`/report/${fileId}`)
  return response.data
}

export async function getAnalysesList() {
  const response = await api.get('/analyses')
  return response.data
}

export async function getAnalysis(fileId: string) {
  const response = await api.get(`/analysis/${fileId}`)
  return response.data
}

export async function deleteAnalysis(fileId: string) {
  const response = await api.delete(`/analysis/${fileId}`)
  return response.data
}

// Combined upload and analyze
export async function uploadAndAnalyze(
  file: File,
  onProgress?: (stage: string) => void
): Promise<AnalysisResult> {
  onProgress?.('Uploading floor plan...')
  const uploadResult = await uploadFloorPlan(file)
  
  onProgress?.('Analyzing structure...')
  const analysisResult = await analyzeFloorPlan(uploadResult.file_id)
  
  return analysisResult
}

export default api
