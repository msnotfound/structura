import { useState, useEffect } from 'react'
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
} from 'lucide-react'

type TabId = 'walls' | 'structural' | 'materials' | 'cost' | 'report' | 'dimensions'

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'walls',       label: 'Walls',     icon: <Layers className="w-4 h-4" /> },
  { id: 'structural',  label: 'Structure', icon: <AlertTriangle className="w-4 h-4" /> },
  { id: 'materials',   label: 'Materials', icon: <Package className="w-4 h-4" /> },
  { id: 'cost',        label: 'Cost',      icon: <Calculator className="w-4 h-4" /> },
  { id: 'report',      label: 'Report',    icon: <FileText className="w-4 h-4" /> },
  { id: 'dimensions',  label: 'Dims',      icon: <Ruler className="w-4 h-4" /> },
]

const STAGE_LABELS: Record<string, string> = {
  idle: 'Ready',
  uploading: 'Uploading image…',
  analyzing: 'Running AI pipeline…',
  complete: 'Analysis complete',
  error: 'Error',
}

function App() {
  const { result, stage, progress, error, analyze, reset } = useAnalysis()
  const [activeTab, setActiveTab] = useState<TabId>('walls')
  const [selectedWallId, setSelectedWallId] = useState<string | undefined>()

  useEffect(() => {
    if (result) setActiveTab('walls')
  }, [result])

  const isLoading = stage === 'uploading' || stage === 'analyzing'
  const hasResult = result !== null

  const handleFileSelect = (file: File) => { analyze(file) }

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
            {hasResult && (
              <button
                onClick={reset}
                className="btn btn-outline flex items-center gap-2 text-xs h-8 px-3"
              >
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
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="container mx-auto px-4 py-6">
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
                Upload an architectural drawing and get full structural analysis, 3D visualization, material recommendations, and cost estimates in seconds.
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
                    {/* Progress dots */}
                    <div className="flex justify-center gap-2 mt-3">
                      {['CV Parsing','Geometry','3D Extrusion','AI Report'].map((s, i) => (
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
                { icon: <AlertTriangle className="w-5 h-5" />, label: 'Structural Analysis', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
                { icon: <Package className="w-5 h-5" />, label: 'Material AI', color: '#22d3ee', bg: 'rgba(34,211,238,0.1)' },
                { icon: <Calculator className="w-5 h-5" />, label: 'Cost Estimate', color: '#a78bfa', bg: 'rgba(167,139,250,0.1)' },
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
                {/* Corner badge */}
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
                  3D View — Click wall to inspect
                </div>
              </div>

              {/* Quick Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '10px', marginTop: '12px' }}>
                <StatCard label="Walls" value={result.geometry_result?.classified_walls?.length ?? 0} color="#3b82f6" />
                <StatCard label="Rooms" value={result.geometry_result?.rooms?.length ?? (result.geometry_result as any)?.room_polygons?.length ?? 0} color="#22d3ee" />
                <StatCard
                  label="Integrity"
                  value={`${(((result.structural_result as any)?.overall_structural_score ?? (result.structural_result as any)?.overall_integrity_score ?? 0) * 100).toFixed(0)}%`}
                  color="#a78bfa"
                />
                <StatCard
                  label="Est. Cost"
                  value={`₹${((result.cost_result?.grand_total ?? 0) / 100000).toFixed(1)}L`}
                  color="#f59e0b"
                />
              </div>
            </div>

            {/* Right — Tabs Panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* Tab bar */}
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
                    }}
                  >
                    {tab.icon}
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* Tab Content */}
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
        Structura · AI Hackathon PS2 Submission · Gemini 2.5 Flash + Cerebras Qwen 3 235B
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

export default App
