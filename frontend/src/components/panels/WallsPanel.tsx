import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { WallTypeBadge } from '@/components/ui/Badge'
import type { GeometryResult, ClassifiedWall } from '@/types'
import { Layers, Grid3X3 } from 'lucide-react'

interface WallsPanelProps {
  geometry: GeometryResult
  selectedWallId?: string
  onWallSelect?: (id: string) => void
}

export function WallsPanel({ geometry, selectedWallId, onWallSelect }: WallsPanelProps) {
  const { classified_walls, junctions, rooms, structural_spine_ids } = geometry

  const wallsByType = {
    load_bearing: classified_walls.filter(w => w.classification === 'load_bearing'),
    structural_spine: classified_walls.filter(w => w.classification === 'structural_spine'),
    partition: classified_walls.filter(w => w.classification === 'partition'),
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
          <h4 className="text-sm font-medium text-muted-foreground mb-2">All Walls</h4>
          <div className="max-h-64 overflow-y-auto space-y-1">
            {classified_walls.map(wall => (
              <WallListItem 
                key={wall.id} 
                wall={wall}
                isSelected={wall.id === selectedWallId}
                onClick={() => onWallSelect?.(wall.id)}
              />
            ))}
          </div>
        </div>

        {/* Rooms */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">Detected Rooms</h4>
          <div className="grid grid-cols-2 gap-2">
            {rooms.map(room => (
              <div key={room.id} className="p-2 bg-muted rounded text-sm">
                <p className="font-medium truncate">{room.name}</p>
                <p className="text-xs text-muted-foreground">{room.area.toFixed(1)} m²</p>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface WallListItemProps {
  wall: ClassifiedWall
  isSelected: boolean
  onClick: () => void
}

function WallListItem({ wall, isSelected, onClick }: WallListItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between p-2 rounded text-left transition-colors ${
        isSelected ? 'bg-primary/10 border border-primary' : 'bg-muted hover:bg-muted/80'
      }`}
    >
      <div className="flex items-center gap-2">
        <span className="text-sm font-mono">{wall.id.slice(0, 8)}</span>
        <WallTypeBadge type={wall.classification} />
      </div>
      <span className="text-xs text-muted-foreground">
        {wall.span_length.toFixed(1)}m
      </span>
    </button>
  )
}
