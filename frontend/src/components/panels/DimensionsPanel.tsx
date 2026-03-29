import { useState, useMemo } from 'react'
import { Ruler } from 'lucide-react'

interface DimensionsPanelProps {
  parseResult: any
  classifiedWalls: any[]
  selectedWallId?: string
  onWallSelect?: (id: string) => void
}

type SortKey = 'id' | 'length_m' | 'thickness_m' | 'classification'
type SortDir = 'asc' | 'desc'

const TYPE_COLORS: Record<string, string> = {
  load_bearing:     '#ef4444',
  structural_spine: '#f59e0b',
  partition:        '#22d3ee',
}

export function DimensionsPanel({ parseResult, classifiedWalls, selectedWallId, onWallSelect }: DimensionsPanelProps) {
  const [sortKey, setSortKey] = useState<SortKey>('id')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [filter, setFilter] = useState('')

  const walls: any[] = parseResult?.walls ?? []

  // Build classification lookup from geometry classified_walls
  const classMap = useMemo(() => {
    const m: Record<string, string> = {}
    classifiedWalls.forEach((cw: any) => {
      const id = cw.wall?.id ?? cw.id
      if (id) m[id] = cw.classification ?? 'partition'
    })
    return m
  }, [classifiedWalls])

  // Enrich walls with classification
  const enriched = useMemo(() => walls.map(w => ({
    ...w,
    classification: classMap[w.id] ?? 'partition',
  })), [walls, classMap])

  // Filter
  const filtered = useMemo(() => {
    if (!filter) return enriched
    const q = filter.toLowerCase()
    return enriched.filter(w =>
      w.id?.toLowerCase().includes(q) ||
      (classMap[w.id] ?? '').includes(q)
    )
  }, [enriched, filter])

  // Sort
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'id') cmp = (a.id ?? '').localeCompare(b.id ?? '')
      else if (sortKey === 'length_m') cmp = (a.length_m ?? 0) - (b.length_m ?? 0)
      else if (sortKey === 'thickness_m') cmp = (a.thickness_m ?? 0) - (b.thickness_m ?? 0)
      else if (sortKey === 'classification') cmp = (a.classification ?? '').localeCompare(b.classification ?? '')
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [filtered, sortKey, sortDir])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const exteriorCount = walls.filter(w => w.is_exterior).length
  const totalLength = walls.reduce((s, w) => s + (w.length_m ?? 0), 0)

  const thStyle: React.CSSProperties = {
    padding: '8px 10px',
    textAlign: 'left',
    fontSize: '0.68rem',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: 'var(--color-muted-foreground)',
    background: 'rgba(255,255,255,0.03)',
    borderBottom: '1px solid rgba(255,255,255,0.07)',
    cursor: 'pointer',
    userSelect: 'none',
    whiteSpace: 'nowrap',
  }

  const SortArrow = ({ k }: { k: SortKey }) => (
    <span style={{ marginLeft: '4px', opacity: sortKey === k ? 1 : 0.3 }}>
      {sortKey === k && sortDir === 'desc' ? '↓' : '↑'}
    </span>
  )

  return (
    <div className="card animate-slide-up" style={{ overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        background: 'rgba(255,255,255,0.02)',
      }}>
        <div className="flex items-center gap-2 mb-2">
          <Ruler className="w-4 h-4" style={{ color: '#22d3ee' }} />
          <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>Wall Dimensions</span>
        </div>
        <p style={{ fontSize: '0.72rem', color: 'var(--color-muted-foreground)' }}>
          {walls.length} walls · {exteriorCount} exterior · {totalLength.toFixed(1)} m total
        </p>
        {/* Filter */}
        <input
          className="input mt-3 h-8 text-xs"
          placeholder="Filter by ID or type…"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          style={{ fontSize: '0.78rem' }}
        />
      </div>

      {/* Table */}
      <div style={{ maxHeight: '450px', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
          <thead>
            <tr>
              <th style={thStyle} onClick={() => handleSort('id')}>ID <SortArrow k="id" /></th>
              <th style={thStyle}>Start (px)</th>
              <th style={thStyle}>End (px)</th>
              <th style={thStyle} onClick={() => handleSort('length_m')}>Length <SortArrow k="length_m" /></th>
              <th style={thStyle} onClick={() => handleSort('thickness_m')}>Thick <SortArrow k="thickness_m" /></th>
              <th style={thStyle} onClick={() => handleSort('classification')}>Type <SortArrow k="classification" /></th>
              <th style={thStyle}>Ext</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((wall, idx) => {
              const isSelected = wall.id === selectedWallId
              const typeColor = TYPE_COLORS[wall.classification] ?? '#64829e'
              return (
                <tr
                  key={wall.id ?? idx}
                  onClick={() => onWallSelect?.(wall.id)}
                  style={{
                    background: isSelected
                      ? 'rgba(59,130,246,0.12)'
                      : idx % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent',
                    borderLeft: isSelected ? '3px solid #3b82f6' : '3px solid transparent',
                    cursor: 'pointer',
                    transition: 'background 0.15s',
                  }}
                >
                  <td style={{ padding: '6px 10px', fontFamily: 'monospace', color: isSelected ? '#60a5fa' : 'var(--color-foreground)', fontWeight: isSelected ? 700 : 400 }}>
                    {wall.id ?? `wall_${idx}`}
                  </td>
                  <td style={{ padding: '6px 10px', color: 'var(--color-muted-foreground)', fontFamily: 'monospace', fontSize: '0.7rem' }}>
                    ({Math.round(wall.start?.x ?? 0)},{Math.round(wall.start?.y ?? 0)})
                  </td>
                  <td style={{ padding: '6px 10px', color: 'var(--color-muted-foreground)', fontFamily: 'monospace', fontSize: '0.7rem' }}>
                    ({Math.round(wall.end?.x ?? 0)},{Math.round(wall.end?.y ?? 0)})
                  </td>
                  <td style={{ padding: '6px 10px', fontWeight: 600 }}>
                    {(wall.length_m ?? 0).toFixed(2)}m
                  </td>
                  <td style={{ padding: '6px 10px', color: 'var(--color-muted-foreground)' }}>
                    {(wall.thickness_m ?? 0).toFixed(3)}m
                  </td>
                  <td style={{ padding: '6px 10px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      background: `${typeColor}18`,
                      color: typeColor,
                      border: `1px solid ${typeColor}33`,
                    }}>
                      {wall.classification === 'load_bearing' ? 'LB' :
                       wall.classification === 'structural_spine' ? 'SP' : 'PT'}
                    </span>
                  </td>
                  <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                    {wall.is_exterior
                      ? <span style={{ color: '#22d3ee', fontWeight: 700, fontSize: '0.7rem' }}>Yes</span>
                      : <span style={{ color: 'var(--color-muted-foreground)', fontSize: '0.7rem' }}>No</span>
                    }
                  </td>
                </tr>
              )
            })}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: 'var(--color-muted-foreground)' }}>
                  No walls match your filter
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
