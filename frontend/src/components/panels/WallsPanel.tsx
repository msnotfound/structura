import { useEffect, useRef, useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { WallTypeBadge } from '@/components/ui/Badge'
import type { GeometryResult } from '@/types'
import { Layers, X, ArrowRight } from 'lucide-react'

interface WallsPanelProps {
  geometry: GeometryResult
  selectedWallId?: string
  onWallSelect?: (id: string | undefined) => void
  parseResult?: any
}

type ApiClassifiedWall = {
  wall?: { id?: string; length_m?: number; is_exterior?: boolean; start?: any; end?: any; thickness_m?: number }
  classification?: string
  reason?: string
  confidence?: number
  adjacent_room_types?: string[]
  id?: string
}

const TYPE_COLORS: Record<string, string> = {
  load_bearing: '#ef4444',
  structural_spine: '#f59e0b',
  partition: '#22d3ee',
}

export function WallsPanel({ geometry, selectedWallId, onWallSelect, parseResult }: WallsPanelProps) {
  const classified_walls: ApiClassifiedWall[] = (geometry.classified_walls as any) ?? []
  const junctions = geometry.junctions ?? []
  const rooms: any[] = (geometry as any).rooms ?? (geometry as any).room_polygons ?? []

  const getWallId   = (w: ApiClassifiedWall) => w.wall?.id ?? w.id ?? ''
  const getWallLength = (w: ApiClassifiedWall) => w.wall?.length_m ?? (w as any).span_length ?? 0
  const getWallClass  = (w: ApiClassifiedWall) => w.classification ?? 'partition'

  // Map raw parseResult walls by id for detail view
  const rawWallMap = useMemo(() => {
    const m: Record<string, any> = {}
    const rawWalls: any[] = parseResult?.walls ?? []
    rawWalls.forEach(w => { if (w.id) m[w.id] = w })
    return m
  }, [parseResult])

  // Selected wall full data
  const selectedClassified = useMemo(() =>
    classified_walls.find(w => getWallId(w) === selectedWallId),
    [classified_walls, selectedWallId]
  )
  const selectedRaw = selectedWallId ? rawWallMap[selectedWallId] : null

  const wallsByType = {
    load_bearing:     classified_walls.filter(w => getWallClass(w) === 'load_bearing'),
    structural_spine: classified_walls.filter(w => getWallClass(w) === 'structural_spine'),
    partition:        classified_walls.filter(w => getWallClass(w) === 'partition'),
  }

  // Scroll selected item into view
  const listRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (selectedWallId && listRef.current) {
      const el = listRef.current.querySelector(`[data-wall-id="${selectedWallId}"]`)
      el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [selectedWallId])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2" style={{ fontSize: '0.9rem' }}>
          <Layers className="w-4 h-4" style={{ color: '#22d3ee' }} />
          Wall Classification
        </CardTitle>
      </CardHeader>
      <CardContent style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

        {/* Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '8px' }}>
          {[
            { key: 'load_bearing', label: 'Load Bearing', count: wallsByType.load_bearing.length, color: '#ef4444' },
            { key: 'structural_spine', label: 'Spine', count: wallsByType.structural_spine.length, color: '#f59e0b' },
            { key: 'partition', label: 'Partition', count: wallsByType.partition.length, color: '#22d3ee' },
          ].map(({ label, count, color }) => (
            <div key={label} style={{
              padding: '12px 8px', borderRadius: '10px', textAlign: 'center',
              background: `${color}12`, border: `1px solid ${color}25`,
            }}>
              <p style={{ fontSize: '1.6rem', fontWeight: 800, color, lineHeight: 1 }}>{count}</p>
              <p style={{ fontSize: '0.65rem', color, fontWeight: 600, marginTop: '4px', opacity: 0.8 }}>{label}</p>
            </div>
          ))}
        </div>

        {/* Quick stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
          {[
            { label: 'Junctions', value: junctions.length },
            { label: 'Rooms Detected', value: rooms.length },
          ].map(({ label, value }) => (
            <div key={label} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 10px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '8px',
              fontSize: '0.78rem',
            }}>
              <span style={{ color: 'var(--color-muted-foreground)' }}>{label}</span>
              <span style={{ fontWeight: 700, color: 'var(--color-foreground)' }}>{value}</span>
            </div>
          ))}
        </div>

        {/* Wall List */}
        <div>
          <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--color-muted-foreground)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            All Walls ({classified_walls.length})
          </p>
          <div ref={listRef} style={{ maxHeight: '220px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '3px' }}>
            {classified_walls.map((wall, idx) => {
              const wallId = getWallId(wall)
              const displayId = wallId || `wall_${idx}`
              const cls = getWallClass(wall)
              const color = TYPE_COLORS[cls] ?? '#64829e'
              const isSelected = displayId === selectedWallId

              return (
                <button
                  key={displayId}
                  data-wall-id={displayId}
                  onClick={() => onWallSelect?.(isSelected ? undefined : displayId)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '7px 10px',
                    borderRadius: '8px',
                    border: isSelected ? `1px solid ${color}50` : '1px solid transparent',
                    background: isSelected ? `${color}12` : 'rgba(255,255,255,0.02)',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                    boxShadow: isSelected ? `0 0 12px ${color}20` : 'none',
                  }}
                  onMouseEnter={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.05)' }}
                  onMouseLeave={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.02)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color, flexShrink: 0 }} />
                    <span style={{ fontFamily: 'monospace', fontSize: '0.78rem', fontWeight: isSelected ? 700 : 400, color: isSelected ? color : 'var(--color-foreground)' }}>
                      {displayId}
                    </span>
                    <WallTypeBadge type={cls as any} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--color-muted-foreground)' }}>
                      {getWallLength(wall).toFixed(1)}m
                    </span>
                    {isSelected && <ArrowRight className="w-3 h-3" style={{ color }} />}
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Selected Wall Detail Drawer */}
        {selectedWallId && (selectedClassified || selectedRaw) && (
          <div style={{
            padding: '14px',
            background: 'rgba(59,130,246,0.06)',
            border: '1px solid rgba(59,130,246,0.2)',
            borderRadius: '12px',
            animation: 'slide-up 0.2s ease',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div>
                <span style={{ fontFamily: 'monospace', fontWeight: 800, color: '#60a5fa', fontSize: '1rem' }}>
                  {selectedWallId}
                </span>
                <span style={{ marginLeft: '8px' }}>
                  <WallTypeBadge type={(getWallClass(selectedClassified!) as any) || 'partition'} />
                </span>
              </div>
              <button
                onClick={() => onWallSelect?.(undefined)}
                style={{ background: 'rgba(255,255,255,0.06)', border: 'none', borderRadius: '6px', padding: '4px', cursor: 'pointer', color: 'var(--color-muted-foreground)' }}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.78rem' }}>
              {selectedRaw?.start && (
                <DetailRow label="Start" value={`(${Math.round(selectedRaw.start.x)}, ${Math.round(selectedRaw.start.y)}) px`} />
              )}
              {selectedRaw?.end && (
                <DetailRow label="End" value={`(${Math.round(selectedRaw.end.x)}, ${Math.round(selectedRaw.end.y)}) px`} />
              )}
              <DetailRow label="Length" value={`${(selectedClassified?.wall?.length_m ?? selectedRaw?.length_m ?? 0).toFixed(2)} m`} />
              <DetailRow label="Thickness" value={`${(selectedClassified?.wall?.thickness_m ?? selectedRaw?.thickness_m ?? 0).toFixed(3)} m`} />
              <DetailRow label="Exterior" value={selectedRaw?.is_exterior ? 'Yes' : 'No'} />
              {selectedClassified?.confidence !== undefined && (
                <DetailRow label="Confidence" value={`${(selectedClassified.confidence * 100).toFixed(0)}%`} />
              )}
            </div>

            {selectedClassified?.reason && (
              <div style={{ marginTop: '10px', padding: '8px 10px', background: 'rgba(255,255,255,0.04)', borderRadius: '8px' }}>
                <p style={{ fontSize: '0.65rem', color: 'var(--color-muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>Classification Reason</p>
                <p style={{ fontSize: '0.76rem', color: 'var(--color-foreground)' }}>{selectedClassified.reason}</p>
              </div>
            )}

            {selectedClassified?.adjacent_room_types && selectedClassified.adjacent_room_types.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <p style={{ fontSize: '0.65rem', color: 'var(--color-muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>Adjacent Rooms</p>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {selectedClassified.adjacent_room_types.map((rt, i) => (
                    <span key={i} style={{
                      padding: '2px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600,
                      background: 'rgba(167,139,250,0.15)', color: '#a78bfa',
                    }}>{rt}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Rooms */}
        {rooms.length > 0 && (
          <div>
            <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--color-muted-foreground)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Detected Rooms
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              {rooms.map((room: any, idx: number) => (
                <div key={room.id ?? idx} style={{
                  padding: '8px 10px',
                  background: 'rgba(167,139,250,0.08)',
                  border: '1px solid rgba(167,139,250,0.15)',
                  borderRadius: '8px',
                }}>
                  <p style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--color-foreground)' }}>
                    {room.room_label ?? room.label ?? room.name ?? room.room_type ?? 'Room'}
                  </p>
                  <p style={{ fontSize: '0.7rem', color: 'var(--color-muted-foreground)' }}>
                    {(room.area_m2 ?? room.area ?? 0).toFixed(1)} m²
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <span style={{ fontSize: '0.65rem', color: 'var(--color-muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</span>
      <span style={{ fontWeight: 600, color: 'var(--color-foreground)', fontFamily: label.includes('px') || label === 'Start' || label === 'End' ? 'monospace' : 'inherit' }}>{value}</span>
    </div>
  )
}
