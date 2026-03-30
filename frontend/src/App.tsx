import { useState, useEffect, useCallback } from 'react'
import {
  FileUpload,
  ThreeViewer,
  ThreeViewerPlaceholder,
  StructuralPanel,
  MaterialsPanel,
  CostPanel,
  ReportPanel,
  WallsPanel,
} from '@/components'
import { DimensionsPanel } from '@/components/panels/DimensionsPanel'
import { LoginPage } from '@/components/LoginPage'
import { useAnalysis } from '@/hooks/useAnalysis'
import {
  Building2,
  RotateCcw,
  Loader2,
  Layers,
  AlertTriangle,
  Package,
  Calculator,
  FileText,
  Ruler,
  Zap,
  Clock,
  LogOut,
  Trash2,
  ChevronRight,
  Compass,
  Hammer,
} from 'lucide-react'

type TabId = 'walls' | 'structural' | 'materials' | 'cost' | 'report' | 'dimensions' | 'vastu' | 'foundation'

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'walls',       label: 'Walls',      icon: <Layers className="w-4 h-4" /> },
  { id: 'structural',  label: 'Structure',  icon: <AlertTriangle className="w-4 h-4" /> },
  { id: 'materials',   label: 'Materials',  icon: <Package className="w-4 h-4" /> },
  { id: 'cost',        label: 'Cost',       icon: <Calculator className="w-4 h-4" /> },
  { id: 'vastu',       label: 'Vastu',      icon: <Compass className="w-4 h-4" /> },
  { id: 'foundation',  label: 'Foundation', icon: <Hammer className="w-4 h-4" /> },
  { id: 'report',      label: 'Report',     icon: <FileText className="w-4 h-4" /> },
  { id: 'dimensions',  label: 'Dims',       icon: <Ruler className="w-4 h-4" /> },
]

const STAGE_LABELS: Record<string, string> = {
  idle: 'Ready',
  uploading: 'Uploading image…',
  analyzing: 'Running AI pipeline…',
  complete: 'Analysis complete',
  error: 'Error',
}

interface AnalysisHistoryItem {
  file_id: string
  analyzed_at: string
  room_count: number
  room_names: string[]
  wall_count: number
  structural_score: number
  total_cost: number
  beam_count: number
  column_count: number
}

interface AuthUser {
  name: string
  email: string
}

function App() {
  const { result, stage, progress, error, analyze, reset, loadFromData } = useAnalysis()
  const [activeTab, setActiveTab] = useState<TabId>('walls')
  const [selectedWallId, setSelectedWallId] = useState<string | undefined>()
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([])

  // Auth state
  const [authToken, setAuthToken] = useState<string | null>(
    localStorage.getItem('auth_token')
  )
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => {
    const stored = localStorage.getItem('auth_user')
    return stored ? JSON.parse(stored) : null
  })

  useEffect(() => {
    if (result) setActiveTab('walls')
  }, [result])

  useEffect(() => {
    if (authToken) fetchHistory()
  }, [authToken])

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch('/api/analyses')
      if (res.ok) {
        const data = await res.json()
        setHistory(data.analyses ?? [])
      }
    } catch { /* ignore */ }
  }, [])

  const handleLogin = useCallback((token: string, user: AuthUser) => {
    setAuthToken(token)
    setAuthUser(user)
  }, [])

  const handleLogout = useCallback(() => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    setAuthToken(null)
    setAuthUser(null)
  }, [])

  const handleDeleteAnalysis = useCallback(async (fileId: string) => {
    try {
      await fetch(`/api/analysis/${fileId}`, { method: 'DELETE' })
      setHistory(h => h.filter(a => a.file_id !== fileId))
    } catch { /* ignore */ }
  }, [])

  const handleLoadAnalysis = useCallback(async (fileId: string) => {
    try {
      const res = await fetch(`/api/analysis/${fileId}`)
      if (res.ok) {
        const data = await res.json()
        loadFromData(data)
        setShowHistory(false)
      }
    } catch(e) {
      console.error('Failed to load analysis:', e)
    }
  }, [loadFromData])

  const isLoading = stage === 'uploading' || stage === 'analyzing'
  const hasResult = result !== null

  const handleFileSelect = (file: File) => {
    analyze(file).then(() => fetchHistory())
  }

  // Show login page if not authenticated
  if (!authToken) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--color-background)' }}>

      {/* ── Header ── */}
      <header style={{
        background: 'linear-gradient(90deg, rgba(5,13,26,0.98) 0%, rgba(12,22,50,0.98) 100%)',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        backdropFilter: 'blur(20px)',
        position: 'sticky', top: 0, zIndex: 50,
      }}>
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div style={{
              background: 'linear-gradient(135deg, #3b82f6, #22d3ee)',
              borderRadius: '12px',
              padding: '8px',
              boxShadow: '0 0 20px rgba(59,130,246,0.3)',
            }}>
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold gradient-text tracking-tight">STRUCTURA</h1>
              <p style={{ fontSize: '0.65rem', color: 'var(--color-muted-foreground)', marginTop: '-2px' }}>
                Autonomous Structural Intelligence
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* History button */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              style={{
                display: 'flex', alignItems: 'center', gap: '5px',
                background: showHistory ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.04)',
                border: showHistory ? '1px solid rgba(59,130,246,0.3)' : '1px solid rgba(255,255,255,0.08)',
                borderRadius: '8px', padding: '5px 10px',
                color: showHistory ? '#60a5fa' : 'var(--color-muted-foreground)',
                fontSize: '0.72rem', fontWeight: 600, cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <Clock className="w-3.5 h-3.5" />
              History{history.length > 0 && ` (${history.length})`}
            </button>

            {hasResult && (
              <button onClick={() => { reset(); fetchHistory() }}
                className="btn btn-outline flex items-center gap-2 text-xs h-8 px-3">
                <RotateCcw className="w-3 h-3" /> New Analysis
              </button>
            )}

            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '20px',
              padding: '4px 10px',
              fontSize: '0.7rem',
              color: 'var(--color-muted-foreground)',
            }}>
              <Zap className="w-3 h-3" style={{ color: '#22d3ee' }} />
              Gemini + Cerebras
            </div>

            {/* User menu */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '20px',
              padding: '4px 10px 4px 12px',
            }}>
              <span style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.7)', fontWeight: 600 }}>
                {authUser?.name}
              </span>
              <button
                onClick={handleLogout}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'rgba(255,255,255,0.3)', display: 'flex',
                }}
                title="Logout"
              >
                <LogOut style={{ width: '14px', height: '14px' }} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="container mx-auto px-4 py-6">
        {/* History Drawer */}
        {showHistory && (
          <div className="animate-slide-up" style={{
            marginBottom: '16px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '14px',
            padding: '16px',
            maxHeight: '300px',
            overflowY: 'auto',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'white' }}>
                Analysis History
              </h3>
              <span style={{ fontSize: '0.72rem', color: 'var(--color-muted-foreground)' }}>
                {history.length} saved
              </span>
            </div>

            {history.length === 0 ? (
              <p style={{ fontSize: '0.82rem', color: 'var(--color-muted-foreground)', textAlign: 'center', padding: '20px' }}>
                No saved analyses yet. Upload a floor plan to get started.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {history.map(item => (
                  <div key={item.file_id} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    borderRadius: '10px',
                    padding: '10px 14px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                    onClick={() => handleLoadAnalysis(item.file_id)}
                    onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(59,130,246,0.3)')}
                    onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)')}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'white' }}>
                          {item.room_names?.join(', ') || `${item.room_count} rooms`}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: '12px', fontSize: '0.7rem', color: 'var(--color-muted-foreground)' }}>
                        <span>{item.wall_count} walls</span>
                        <span>{item.beam_count} beams</span>
                        <span>{((item.structural_score || 0) * 100).toFixed(0)}% integrity</span>
                        <span>₹{((item.total_cost || 0) / 100000).toFixed(1)}L</span>
                        <span>{new Date(item.analyzed_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <button
                        onClick={e => {
                          e.stopPropagation()
                          handleDeleteAnalysis(item.file_id)
                        }}
                        style={{
                          background: 'rgba(239,68,68,0.1)',
                          border: '1px solid rgba(239,68,68,0.2)',
                          borderRadius: '6px',
                          padding: '4px 6px',
                          cursor: 'pointer',
                          color: '#f87171',
                          display: 'flex',
                        }}
                        title="Delete analysis"
                      >
                        <Trash2 style={{ width: '12px', height: '12px' }} />
                      </button>
                      <ChevronRight style={{ width: '14px', height: '14px', color: 'rgba(255,255,255,0.3)' }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {!hasResult ? (
          /* ── Upload View ── */
          <div className="max-w-2xl mx-auto animate-slide-up">

            {/* Hero */}
            <div className="text-center mb-8 pt-8">
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'rgba(59,130,246,0.1)',
                border: '1px solid rgba(59,130,246,0.2)',
                borderRadius: '20px',
                padding: '4px 14px',
                marginBottom: '20px',
                fontSize: '0.75rem',
                color: '#60a5fa',
              }}>
                <Zap className="w-3 h-3" /> AI-powered floor plan analysis
              </div>
              <h2 style={{
                fontSize: '2.5rem', fontWeight: 800, lineHeight: 1.15,
                marginBottom: '12px',
              }}>
                <span className="gradient-text">Analyze</span> your<br />floor plan instantly
              </h2>
              <p style={{ color: 'var(--color-muted-foreground)', fontSize: '1rem', maxWidth: '460px', margin: '0 auto' }}>
                Upload an architectural drawing and get full structural analysis, 3D visualization with IS 456 beam/column design, material recommendations, and cost estimates.
              </p>
            </div>

            {/* Upload card */}
            <div className="card glass p-6">
              <FileUpload onFileSelect={handleFileSelect} isLoading={isLoading} />

              {isLoading && (
                <div className="mt-6 animate-slide-up">
                  <div style={{
                    background: 'rgba(59,130,246,0.08)',
                    border: '1px solid rgba(59,130,246,0.2)',
                    borderRadius: '12px',
                    padding: '16px 20px',
                    textAlign: 'center',
                  }}>
                    <div className="flex items-center justify-center gap-3 mb-3">
                      <Loader2 className="w-5 h-5 animate-spin" style={{ color: '#3b82f6' }} />
                      <span style={{ color: '#60a5fa', fontWeight: 600 }}>
                        {STAGE_LABELS[stage] ?? 'Processing…'}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-muted-foreground)' }}>{progress}</p>
                    <div className="flex justify-center gap-2 mt-3">
                      {['CV Parsing','Geometry','3D + Beams','AI Report'].map((s, i) => (
                        <div key={s} style={{
                          height: '4px', width: '40px', borderRadius: '4px',
                          background: stage === 'analyzing' && i < 2 ? '#3b82f6' : 'rgba(255,255,255,0.1)',
                          transition: 'background 0.5s ease',
                        }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="mt-4 animate-slide-up" style={{
                  background: 'rgba(239,68,68,0.08)',
                  border: '1px solid rgba(239,68,68,0.2)',
                  borderRadius: '12px',
                  padding: '16px',
                }}>
                  <p style={{ color: '#f87171', fontSize: '0.875rem' }}>{error}</p>
                  <button onClick={reset} className="btn btn-outline mt-2 h-8 text-xs">Try Again</button>
                </div>
              )}
            </div>

            {/* Feature grid */}
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginTop: '24px',
            }}>
              {[
                { icon: <Layers className="w-5 h-5" />, label: 'Wall Classification', color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
                { icon: <AlertTriangle className="w-5 h-5" />, label: 'IS 456 Beam Design', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
                { icon: <Package className="w-5 h-5" />, label: 'Material AI', color: '#22d3ee', bg: 'rgba(34,211,238,0.1)' },
                { icon: <Calculator className="w-5 h-5" />, label: 'CPWD Cost DB', color: '#a78bfa', bg: 'rgba(167,139,250,0.1)' },
              ].map((f) => (
                <div key={f.label} style={{
                  padding: '16px 12px',
                  background: f.bg,
                  border: `1px solid ${f.color}22`,
                  borderRadius: '12px',
                  textAlign: 'center',
                }}>
                  <div style={{ color: f.color, display: 'flex', justifyContent: 'center', marginBottom: '8px' }}>
                    {f.icon}
                  </div>
                  <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--color-foreground)' }}>{f.label}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* ── Results View ── */
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '20px' }} className="animate-slide-up">

            {/* Left — 3D Viewer + Stats */}
            <div>
              <div style={{
                borderRadius: '16px',
                overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.07)',
                height: '500px',
                position: 'relative',
              }}>
                {result.scene_graph ? (
                  <ThreeViewer
                    sceneGraph={result.scene_graph}
                    selectedWallId={selectedWallId}
                    onWallSelect={setSelectedWallId}
                    className="w-full h-full"
                  />
                ) : (
                  <ThreeViewerPlaceholder className="w-full h-full" />
                )}
                <div style={{
                  position: 'absolute', top: '12px', left: '12px',
                  background: 'rgba(5,13,26,0.8)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  padding: '4px 10px',
                  fontSize: '0.7rem',
                  color: 'var(--color-muted-foreground)',
                }}>
                  3D View — Click wall/beam/column to inspect
                </div>
              </div>

              {/* Quick Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: '8px', marginTop: '12px' }}>
                <StatCard label="Walls" value={result.geometry_result?.classified_walls?.length ?? 0} color="#3b82f6" />
                <StatCard label="Rooms" value={result.geometry_result?.rooms?.length ?? (result.geometry_result as any)?.room_polygons?.length ?? 0} color="#22d3ee" />
                <StatCard
                  label="Integrity"
                  value={`${(((result.structural_result as any)?.overall_structural_score ?? (result.structural_result as any)?.overall_integrity_score ?? 0) * 100).toFixed(0)}%`}
                  color="#a78bfa"
                />
                <StatCard
                  label="Beams"
                  value={(result.scene_graph as any)?.beams?.length ?? 0}
                  color="#3b82f6"
                />
                <StatCard
                  label="Vastu"
                  value={`${(result as any).vastu_result?.overall_score ?? '—'}%`}
                  color="#22c55e"
                />
                <StatCard
                  label="Est. Cost"
                  value={`₹${((result.cost_result?.grand_total ?? 0) / 100000).toFixed(1)}L`}
                  color="#f59e0b"
                />
              </div>
              {/* Download Report */}
              <button
                onClick={() => {
                  const r = result as any
                  const lines = [
                    '═══════════════════════════════════════════════════',
                    '  STRUCTURA — Structural Intelligence Report',
                    '  Generated: ' + new Date().toLocaleString(),
                    '═══════════════════════════════════════════════════',
                    '',
                    '▸ ROOMS DETECTED: ' + (r.parse_result?.rooms?.length ?? 0),
                    ...(r.parse_result?.rooms ?? []).map((rm: any) =>
                      `  • ${rm.label} — ${rm.area_m2?.toFixed(1)} m² (${rm.room_type})`
                    ),
                    '',
                    '▸ STRUCTURAL ANALYSIS',
                    `  Walls: ${r.geometry_result?.classified_walls?.length ?? 0}`,
                    `  Beams: ${r.scene_graph?.beams?.length ?? 0}`,
                    `  Columns: ${r.scene_graph?.columns?.length ?? 0}`,
                    `  Integrity Score: ${((r.structural_result?.overall_structural_score ?? 0) * 100).toFixed(0)}%`,
                    '',
                    '▸ VASTU COMPLIANCE: ' + (r.vastu_result?.overall_score ?? 'N/A') + '%',
                    ...(r.vastu_result?.results ?? []).map((v: any) =>
                      `  ${v.status} ${v.room_label} — ${v.actual_direction} (Ideal: ${v.ideal_direction})`
                    ),
                    '',
                    '▸ FOUNDATION DESIGN (IS 1904)',
                    `  Soil: ${r.foundation_result?.soil_type ?? 'N/A'}`,
                    `  Footings: ${r.foundation_result?.total_footings ?? 0} (${r.foundation_result?.safe_count ?? 0} safe)`,
                    `  Concrete: ${r.foundation_result?.total_concrete_cum ?? 0} m³`,
                    `  Steel: ${r.foundation_result?.total_steel_kg ?? 0} kg`,
                    '',
                    '▸ PLINTH AREA',
                    `  Built-up: ${r.plinth_result?.built_up_area?.sqm?.toFixed(1) ?? 'N/A'} m² (${r.plinth_result?.built_up_area?.sqft?.toFixed(0) ?? 'N/A'} sqft)`,
                    `  Carpet: ${r.plinth_result?.carpet_area?.sqm?.toFixed(1) ?? 'N/A'} m²`,
                    `  FAR: ${r.plinth_result?.far?.toFixed(2) ?? 'N/A'}`,
                    '',
                    '▸ COST ESTIMATION',
                    `  Grand Total: ₹${(r.cost_result?.grand_total ?? 0).toLocaleString()}`,
                    `  Per sqm: ₹${(r.cost_result?.cost_per_sqm ?? 0).toLocaleString()}`,
                    `  Budget: ₹${(r.cost_result?.budget_total ?? 0).toLocaleString()}`,
                    `  Premium: ₹${(r.cost_result?.premium_total ?? 0).toLocaleString()}`,
                    '',
                    ...(r.cost_result?.category_totals ?? []).map((c: any) =>
                      `  ${c.category}: ₹${c.total_cost?.toLocaleString()} (${c.percentage?.toFixed(1)}%)`
                    ),
                    '',
                    '▸ AI REPORT',
                    r.report?.full_report ?? r.report?.executive_summary ?? 'N/A',
                    '',
                    '═══════════════════════════════════════════════════',
                    '  IS 456:2000 | IS 1904:1986 | Vastu Shastra',
                    '  Team TylerDurden · IIIT Naya Raipur',
                    '═══════════════════════════════════════════════════',
                  ]
                  const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `structura-report-${new Date().toISOString().slice(0,10)}.txt`
                  a.click()
                  URL.revokeObjectURL(url)
                }}
                style={{
                  marginTop: '8px', width: '100%', padding: '10px',
                  background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(34,211,238,0.1))',
                  border: '1px solid rgba(59,130,246,0.3)', borderRadius: '10px',
                  color: '#60a5fa', fontWeight: 700, fontSize: '0.8rem',
                  cursor: 'pointer', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', gap: '8px',
                  transition: 'all 0.2s',
                }}
                onMouseOver={e => (e.currentTarget.style.background = 'linear-gradient(135deg, rgba(59,130,246,0.25), rgba(34,211,238,0.15))')}
                onMouseOut={e => (e.currentTarget.style.background = 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(34,211,238,0.1))')}
              >
                <FileText className="w-4 h-4" /> Download Full Report
              </button>
            </div>

            {/* Right — Tabs Panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: `repeat(${TABS.length}, 1fr)`,
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: '12px',
                padding: '4px',
                gap: '2px',
              }}>
                {TABS.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center',
                      justifyContent: 'center', gap: '3px',
                      padding: '7px 4px',
                      borderRadius: '8px',
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      transition: 'all 0.2s ease',
                      background: activeTab === tab.id
                        ? 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(34,211,238,0.15))'
                        : 'transparent',
                      color: activeTab === tab.id ? '#60a5fa' : 'var(--color-muted-foreground)',
                      border: activeTab === tab.id ? '1px solid rgba(59,130,246,0.25)' : '1px solid transparent',
                      boxShadow: activeTab === tab.id ? '0 2px 8px rgba(59,130,246,0.15)' : 'none',
                      cursor: 'pointer',
                    }}
                  >
                    {tab.icon}
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>

              <div style={{ maxHeight: '580px', overflowY: 'auto', overflowX: 'hidden' }}>
                {activeTab === 'walls' && (
                  <WallsPanel
                    geometry={result.geometry_result}
                    selectedWallId={selectedWallId}
                    onWallSelect={setSelectedWallId}
                    parseResult={result.parse_result}
                  />
                )}
                {activeTab === 'structural' && (
                  <StructuralPanel result={result.structural_result} />
                )}
                {activeTab === 'materials' && (
                  <MaterialsPanel result={result.materials_result} />
                )}
                {activeTab === 'cost' && (
                  <CostPanel cost={result.cost_result} />
                )}
                {activeTab === 'report' && (
                  <ReportPanel report={result.report} />
                )}
                {activeTab === 'vastu' && (
                  <VastuPanel data={(result as any).vastu_result} />
                )}
                {activeTab === 'foundation' && (
                  <FoundationPanel
                    foundation={(result as any).foundation_result}
                    plinth={(result as any).plinth_result}
                  />
                )}
                {activeTab === 'dimensions' && (
                  <DimensionsPanel
                    parseResult={result.parse_result}
                    classifiedWalls={(result.geometry_result?.classified_walls as any[]) ?? []}
                    selectedWallId={selectedWallId}
                    onWallSelect={setSelectedWallId}
                  />
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ── Footer ── */}
      <footer style={{
        borderTop: '1px solid rgba(255,255,255,0.06)',
        marginTop: '32px',
        padding: '16px',
        textAlign: 'center',
        fontSize: '0.75rem',
        color: 'var(--color-muted-foreground)',
      }}>
        Structura · AI Hackathon PS2 · Gemini 2.5 Flash + Cerebras Qwen 3 235B · IS 456:2000 Compliant
      </footer>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div style={{
      padding: '14px 12px',
      background: `${color}10`,
      border: `1px solid ${color}25`,
      borderRadius: '12px',
      textAlign: 'center',
      borderTop: `2px solid ${color}`,
    }}>
      <p style={{ fontSize: '1.3rem', fontWeight: 700, color, marginBottom: '2px' }}>{value}</p>
      <p style={{ fontSize: '0.7rem', color: 'var(--color-muted-foreground)', fontWeight: 500 }}>{label}</p>
    </div>
  )
}

function VastuPanel({ data }: { data: any }) {
  if (!data) return <div style={{ padding: 16, color: '#999', fontSize: 13 }}>No Vastu data available</div>
  const results = data.results ?? []
  const score = data.overall_score ?? 0
  const scoreColor = score >= 70 ? '#22c55e' : score >= 40 ? '#f59e0b' : '#ef4444'

  return (
    <div style={{ padding: '12px' }}>
      {/* Score header */}
      <div style={{
        background: `${scoreColor}10`, border: `1px solid ${scoreColor}30`,
        borderRadius: 12, padding: '16px', textAlign: 'center', marginBottom: 12,
      }}>
        <p style={{ fontSize: '2rem', fontWeight: 800, color: scoreColor }}>{score}%</p>
        <p style={{ fontSize: 11, color: '#ccc', marginTop: 2 }}>Vastu Shastra Compliance</p>
        <p style={{ fontSize: 10, color: '#888', marginTop: 4 }}>{data.summary}</p>
      </div>

      {/* Rules */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {results.map((r: any, i: number) => (
          <div key={i} style={{
            background: r.compliant ? 'rgba(34,197,94,0.06)' : 'rgba(239,68,68,0.06)',
            border: `1px solid ${r.compliant ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`,
            borderRadius: 10, padding: '10px 12px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, fontSize: 12, color: '#e0e0e0' }}>{r.room_label}</span>
              <span style={{
                fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 6,
                background: r.compliant ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                color: r.compliant ? '#22c55e' : '#ef4444',
              }}>{r.status}</span>
            </div>
            <p style={{ fontSize: 10, color: '#aaa', marginTop: 4 }}>{r.description}</p>
            <p style={{ fontSize: 10, color: '#78a0dc', marginTop: 3 }}>
              Direction: <strong>{r.actual_direction}</strong> (Ideal: {r.ideal_direction})
            </p>
            <p style={{ fontSize: 10, color: r.compliant ? '#6ee7a0' : '#fca5a5', marginTop: 2 }}>{r.recommendation}</p>
          </div>
        ))}
      </div>
      {results.length === 0 && (
        <p style={{ color: '#888', fontSize: 12, textAlign: 'center', padding: 20 }}>
          No rooms with known Vastu rules detected
        </p>
      )}
    </div>
  )
}

function FoundationPanel({ foundation, plinth }: { foundation: any; plinth: any }) {
  if (!foundation && !plinth) return <div style={{ padding: 16, color: '#999', fontSize: 13 }}>No foundation data</div>

  return (
    <div style={{ padding: '12px' }}>
      {/* Plinth Area */}
      {plinth && (
        <div style={{
          background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.2)',
          borderRadius: 12, padding: 14, marginBottom: 12,
        }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: '#60a5fa', marginBottom: 10 }}>📐 Plinth Area Calculation</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 11 }}>
            {[
              ['Built-up Area', `${plinth.built_up_area?.sqm?.toFixed(1)} m² (${plinth.built_up_area?.sqft?.toFixed(0)} sqft)`],
              ['Carpet Area', `${plinth.carpet_area?.sqm?.toFixed(1)} m² (${plinth.carpet_area?.sqft?.toFixed(0)} sqft)`],
              ['Super Built-up', `${plinth.super_built_up_sqm?.toFixed(1)} m² (${plinth.super_built_up_sqft?.toFixed(0)} sqft)`],
              ['Wall Area', `${plinth.wall_area_sqm?.toFixed(1)} m²`],
              ['FAR', plinth.far?.toFixed(2)],
              ['Ground Coverage', `${plinth.ground_coverage_percent?.toFixed(1)}%`],
            ].map(([label, val]) => (
              <div key={String(label)}>
                <span style={{ color: '#888' }}>{label}: </span>
                <span style={{ color: '#e0e0e0', fontWeight: 600 }}>{val}</span>
              </div>
            ))}
          </div>
          <p style={{ fontSize: 10, marginTop: 8, color: plinth.far <= 2.5 ? '#22c55e' : '#ef4444', fontWeight: 600 }}>
            {plinth.far_status}
          </p>
        </div>
      )}

      {/* Foundation Design */}
      {foundation && (
        <>
          <div style={{
            background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)',
            borderRadius: 12, padding: 14, marginBottom: 12,
          }}>
            <h3 style={{ fontSize: 13, fontWeight: 700, color: '#f59e0b', marginBottom: 8 }}>🏗 Foundation Design (IS 1904)</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 11 }}>
              <div><span style={{ color: '#888' }}>Soil Type: </span><span style={{ color: '#e0e0e0' }}>{foundation.soil_type}</span></div>
              <div><span style={{ color: '#888' }}>SBC: </span><span style={{ color: '#e0e0e0' }}>{foundation.net_sbc_kpa} kPa</span></div>
              <div><span style={{ color: '#888' }}>Depth: </span><span style={{ color: '#e0e0e0' }}>{foundation.foundation_depth_m}m</span></div>
              <div><span style={{ color: '#888' }}>Grade: </span><span style={{ color: '#e0e0e0' }}>{foundation.concrete_grade} + {foundation.steel_grade}</span></div>
              <div><span style={{ color: '#888' }}>Concrete: </span><span style={{ color: '#e0e0e0' }}>{foundation.total_concrete_cum} m³</span></div>
              <div><span style={{ color: '#888' }}>Steel: </span><span style={{ color: '#e0e0e0' }}>{foundation.total_steel_kg} kg</span></div>
            </div>
          </div>

          <h4 style={{ fontSize: 12, fontWeight: 700, color: '#ccc', marginBottom: 8 }}>
            Footings ({foundation.safe_count}/{foundation.total_footings} safe)
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {(foundation.footings ?? []).slice(0, 10).map((f: any) => (
              <div key={f.footing_id} style={{
                background: f.safe ? 'rgba(34,197,94,0.05)' : 'rgba(239,68,68,0.05)',
                border: `1px solid ${f.safe ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)'}`,
                borderRadius: 8, padding: '8px 10px', fontSize: 10,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 700, color: '#e0e0e0' }}>{f.footing_id}</span>
                  <span style={{ color: f.safe ? '#22c55e' : '#ef4444', fontWeight: 700 }}>{f.status}</span>
                </div>
                <div style={{ color: '#aaa', marginTop: 3 }}>
                  {f.size} · Depth: {f.depth_m}m · Load: {f.axial_load_kn} kN · Pressure: {f.gross_pressure_kpa} kPa
                </div>
                <div style={{ color: '#78a0dc', marginTop: 2 }}>{f.rebar}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default App

