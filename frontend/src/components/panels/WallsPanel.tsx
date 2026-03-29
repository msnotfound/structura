import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { WallTypeBadge } from '@/components/ui/Badge'
import type { GeometryResult } from '@/types'
import { Layers } from 'lucide-react'

interface WallsPanelProps {
  geometry: GeometryResult
  selectedWallId?: string
  onWallSelect?: (id: string) => void
}

// The API returns classified walls as: { wall: {id, start, end, length_m, ...}, classification, reason, confidence }
type ApiClassifiedWall = {
  wall?: { id?: string; length_m?: number; is_exterior?: boolean }
  classification?: string
  reason?: string
  confidence?: number
  // Also support flat shape for forward compat
  id?: string
  span_length?: number
}

export function WallsPanel({ geometry, selectedWallId, onWallSelect }: WallsPanelProps) {
  const classified_walls: ApiClassifiedWall[] = (geometry.classified_walls as any) ?? []
  const junctions = geometry.junctions ?? []
  const rooms = geometry.rooms ?? []

  const getWallId = (w: ApiClassifiedWall) => w.wall?.id ?? w.id ?? ''
  const getWallLength = (w: ApiClassifiedWall) => w.wall?.length_m ?? (w as any).span_length ?? 0
  const getWallClass = (w: ApiClassifiedWall) => w.classification ?? 'partition'

  const wallsByType = {
    load_bearing: classified_walls.filter(w => getWallClass(w) === 'load_bearing'),
    structural_spine: classified_walls.filter(w => getWallClass(w) === 'structural_spine'),
    partition: classified_walls.filter(w => getWallClass(w) === 'partition'),
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Layers className="w-5 h-5" />
          Wall Classification
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">{wallsByType.load_bearing.length}</p>
            <p className="text-xs text-red-600">Load Bearing</p>
          </div>
          <div className="p-3 bg-yellow-50 rounded-lg">
            <p className="text-2xl font-bold text-yellow-600">{wallsByType.structural_spine.length}</p>
            <p className="text-xs text-yellow-600">Structural Spine</p>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <p className="text-2xl font-bold text-green-600">{wallsByType.partition.length}</p>
            <p className="text-xs text-green-600">Partition</p>
          </div>
        </div>

        {/* Additional Stats */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">Junctions</span>
            <span className="font-medium">{junctions.length}</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-muted rounded">
            <span className="text-muted-foreground">Rooms</span>
            <span className="font-medium">{rooms.length}</span>
          </div>
        </div>

        {/* Walls List */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">All Walls ({classified_walls.length})</h4>
          <div className="max-h-64 overflow-y-auto space-y-1">
            {classified_walls.map((wall, idx) => {
              const wallId = getWallId(wall)
              const displayId = wallId || `wall_${idx}`
              return (
                <button
                  key={displayId}
                  onClick={() => onWallSelect?.(displayId)}
                  className={`w-full flex items-center justify-between p-2 rounded text-left transition-colors ${
                    displayId === selectedWallId
                      ? 'bg-primary/10 border border-primary'
                      : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono">{displayId.slice(0, 10)}</span>
                    <WallTypeBadge type={getWallClass(wall) as any} />
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {getWallLength(wall).toFixed(1)}m
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Rooms */}
        {rooms.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-2">Detected Rooms</h4>
            <div className="grid grid-cols-2 gap-2">
              {rooms.map((room: any, idx: number) => (
                <div key={room.id ?? idx} className="p-2 bg-muted rounded text-sm">
                  <p className="font-medium truncate">{room.name ?? room.type ?? 'Room'}</p>
                  <p className="text-xs text-muted-foreground">{(room.area ?? 0).toFixed(1)} m²</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
