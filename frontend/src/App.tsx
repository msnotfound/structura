import { useState } from 'react'
import { 
  FileUpload, 
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  ThreeViewer, 
  ThreeViewerPlaceholder,
  StructuralPanel,
  MaterialsPanel,
  CostPanel,
  ReportPanel,
  WallsPanel,
} from '@/components'
import { useAnalysis } from '@/hooks/useAnalysis'
import { 
  Building2, 
  RotateCcw, 
  Loader2,
  Layers,
  AlertTriangle,
  Package,
  Calculator,
  FileText
} from 'lucide-react'

type TabId = 'walls' | 'structural' | 'materials' | 'cost' | 'report'

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'walls', label: 'Walls', icon: <Layers className="w-4 h-4" /> },
  { id: 'structural', label: 'Structure', icon: <AlertTriangle className="w-4 h-4" /> },
  { id: 'materials', label: 'Materials', icon: <Package className="w-4 h-4" /> },
  { id: 'cost', label: 'Cost', icon: <Calculator className="w-4 h-4" /> },
  { id: 'report', label: 'Report', icon: <FileText className="w-4 h-4" /> },
]

function App() {
  const { result, stage, progress, error, analyze, reset } = useAnalysis()
  const [activeTab, setActiveTab] = useState<TabId>('walls')
  const [selectedWallId, setSelectedWallId] = useState<string | undefined>()

  const isLoading = stage === 'uploading' || stage === 'analyzing'
  const hasResult = result !== null

  const handleFileSelect = (file: File) => {
    analyze(file)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Building2 className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">Structura</h1>
                <p className="text-xs text-muted-foreground">Autonomous Structural Intelligence</p>
              </div>
            </div>
            
            {hasResult && (
              <Button variant="outline" onClick={reset}>
                <RotateCcw className="w-4 h-4 mr-2" />
                New Analysis
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {!hasResult ? (
          /* Upload View */
          <div className="max-w-2xl mx-auto">
            <Card>
              <CardHeader className="text-center">
                <CardTitle>Analyze Floor Plan</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Upload a floor plan image to get structural analysis, material recommendations, and cost estimates
                </p>
              </CardHeader>
              <CardContent>
                <FileUpload onFileSelect={handleFileSelect} isLoading={isLoading} />
                
                {isLoading && (
                  <div className="mt-6 text-center">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
                    <p className="mt-2 text-sm text-muted-foreground">{progress}</p>
                  </div>
                )}

                {error && (
                  <div className="mt-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
                    <p className="text-sm text-destructive">{error}</p>
                    <Button variant="outline" size="sm" onClick={reset} className="mt-2">
                      Try Again
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Features */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              {[
                { icon: <Layers className="w-5 h-5" />, label: 'Wall Classification' },
                { icon: <AlertTriangle className="w-5 h-5" />, label: 'Structural Analysis' },
                { icon: <Package className="w-5 h-5" />, label: 'Material Suggestions' },
                { icon: <Calculator className="w-5 h-5" />, label: 'Cost Estimation' },
              ].map((feature, idx) => (
                <div key={idx} className="p-4 bg-card border rounded-lg text-center">
                  <div className="text-primary mb-2 flex justify-center">{feature.icon}</div>
                  <p className="text-sm font-medium">{feature.label}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Results View */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 3D Viewer */}
            <div className="lg:col-span-2">
              <Card className="p-0 overflow-hidden">
                <div className="h-[500px]">
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
                </div>
              </Card>

              {/* Quick Stats */}
              <div className="grid grid-cols-4 gap-4 mt-4">
                <StatCard 
                  label="Walls" 
                  value={result.geometry_result?.classified_walls?.length ?? 0} 
                />
                <StatCard 
                  label="Rooms" 
                  value={result.geometry_result?.rooms?.length ?? result.geometry_result?.load_bearing_wall_count ?? 0} 
                />
                <StatCard 
                  label="Integrity" 
                  value={`${(((result.structural_result as any)?.overall_structural_score ?? (result.structural_result as any)?.overall_integrity_score ?? 0) * 100).toFixed(0)}%`} 
                />
                <StatCard 
                  label="Est. Cost" 
                  value={`₹${((result.cost_result?.grand_total ?? 0) / 100000).toFixed(1)}L`} 
                />
              </div>
            </div>

            {/* Right Panel */}
            <div className="space-y-4">
              {/* Tabs */}
              <div className="flex gap-1 p-1 bg-muted rounded-lg">
                {TABS.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      activeTab === tab.id
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {tab.icon}
                    <span className="hidden sm:inline">{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="max-h-[600px] overflow-y-auto">
                {activeTab === 'walls' && (
                  <WallsPanel 
                    geometry={result.geometry_result}
                    selectedWallId={selectedWallId}
                    onWallSelect={setSelectedWallId}
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
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t bg-card mt-auto">
        <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
          Structura - PS2 Hackathon Submission
        </div>
      </footer>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="p-3 bg-card border rounded-lg text-center">
      <p className="text-lg font-bold text-foreground">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}

export default App
