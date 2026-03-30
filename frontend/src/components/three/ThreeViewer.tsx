import { useRef, useMemo, useState, useCallback } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Html, Environment } from '@react-three/drei'
import type { SceneGraph, WallClassification } from '@/types'
import * as THREE from 'three'

const WALL_COLORS: Record<WallClassification, string> = {
  load_bearing:     '#c0392b',
  partition:        '#7fb3d8',
  structural_spine: '#e67e22',
}

const WALL_LABELS: Record<WallClassification, string> = {
  load_bearing:     'Load Bearing',
  partition:        'Partition',
  structural_spine: 'Structural Spine',
}

type ApiWall = {
  wall_id: string
  vertices_3d?: { x: number; y: number; z: number }[]
  vertices?: { x: number; y: number; z: number }[]
  faces?: { vertices: number[] }[]
  classification: WallClassification
  color?: string
  is_exterior?: boolean
  thickness_m?: number
}

type ApiBeam = {
  beam_id: string; start: { x: number; y: number; z: number }; end: { x: number; y: number; z: number }
  width_m: number; depth_m: number; span_m: number
  steel_area_mm2?: number; tension_bars?: string; stirrup_spacing_mm?: number; stirrup_description?: string
  concrete_grade?: string; steel_grade?: string
  total_load_kn_per_m?: number; max_bending_moment_knm?: number; max_shear_force_kn?: number
  deflection_ok?: boolean; color?: string; room_id?: string
}

type ApiColumn = {
  column_id: string; position: { x: number; y: number; z: number }
  width_m: number; depth_m: number; height_m: number
  axial_load_kn?: number; steel_area_mm2?: number; steel_bars?: string
  tie_spacing_mm?: number; load_ratio?: number; color?: string
}

type ApiSlab = {
  id: string; vertices_3d: { x: number; y: number; z: number }[]; elevation: number
  type: string; thickness_m: number; room_id?: string
}

interface ViewerFilters {
  showWalls: boolean; showBeams: boolean; showColumns: boolean; showSlabs: boolean; showLabels: boolean
}

// ── Wall Mesh ──────────────────────────────────────────
function WallMesh({ wall, selected, onSelect }: { wall: ApiWall; selected?: boolean; onSelect?: (id: string) => void }) {
  const verts = wall.vertices_3d ?? wall.vertices ?? []
  const faces = wall.faces ?? []
  const isExterior = wall.is_exterior ?? false
  const classification = wall.classification as WallClassification
  const color = isExterior ? '#8d6e63' : (WALL_COLORS[classification] ?? '#999')

  const geometry = useMemo(() => {
    if (!verts.length || !faces.length) return null
    try {
      const geo = new THREE.BufferGeometry()
      const positions: number[] = []
      verts.forEach(v => positions.push(v.x, v.y, v.z))
      const indices: number[] = []
      faces.forEach(face => { if (face.vertices?.length >= 3) indices.push(...face.vertices) })
      geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
      geo.setIndex(indices)
      geo.computeVertexNormals()
      return geo
    } catch { return null }
  }, [wall.wall_id])

  const labelPos = useMemo(() => {
    if (!verts.length) return [0, 3, 0] as [number, number, number]
    const cx = verts.reduce((s, v) => s + v.x, 0) / verts.length
    const cy = verts.reduce((s, v) => s + v.y, 0) / verts.length
    const cz = verts.reduce((s, v) => s + v.z, 0) / verts.length
    return [cx, cy + 0.4, cz] as [number, number, number]
  }, [wall.wall_id])

  if (!geometry) return null

  return (
    <group>
      <mesh geometry={geometry} onClick={e => { e.stopPropagation(); onSelect?.(wall.wall_id) }} castShadow receiveShadow>
        <meshStandardMaterial
          color={color}
          emissive={selected ? color : '#000'}
          emissiveIntensity={selected ? 0.3 : 0}
          opacity={0.92} transparent side={THREE.DoubleSide}
          metalness={0.05} roughness={0.9}
        />
      </mesh>
      {selected && (
        <>
          <lineSegments geometry={new THREE.EdgesGeometry(geometry)}>
            <lineBasicMaterial color="#ffffff" linewidth={1} />
          </lineSegments>
          <Html position={labelPos} center style={{ pointerEvents: 'none' }}>
            <div style={tooltipStyle(color)}>
              <div style={{ fontWeight: 800, color, fontSize: '12px', marginBottom: '3px' }}>{wall.wall_id}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#ccc', fontSize: '10px' }}>
                <span style={{ width: 6, height: 6, borderRadius: 3, background: color, display: 'inline-block' }} />
                {WALL_LABELS[classification] ?? classification}
                {isExterior && <span style={{ color: '#8d6e63' }}> · Exterior</span>}
              </div>
              {wall.thickness_m && <div style={{ color: '#aaa', fontSize: '10px', marginTop: '2px' }}>Thickness: {(wall.thickness_m * 1000).toFixed(0)}mm</div>}
            </div>
          </Html>
        </>
      )}
    </group>
  )
}

// ── Floor Slab Mesh ─────────────────────────────────────
function SlabMesh({ slab }: { slab: ApiSlab }) {
  const geometry = useMemo(() => {
    if (!slab.vertices_3d || slab.vertices_3d.length < 3) return null
    const shape = new THREE.Shape()
    shape.moveTo(slab.vertices_3d[0].x, slab.vertices_3d[0].z)
    for (let i = 1; i < slab.vertices_3d.length; i++) {
      shape.lineTo(slab.vertices_3d[i].x, slab.vertices_3d[i].z)
    }
    shape.closePath()
    const geo = new THREE.ShapeGeometry(shape)
    return geo
  }, [slab.id])

  if (!geometry) return null

  return (
    <mesh geometry={geometry} rotation={[-Math.PI / 2, 0, 0]} position={[0, slab.elevation + 0.01, 0]} receiveShadow>
      <meshStandardMaterial color="#1a2a4a" opacity={0.6} transparent side={THREE.DoubleSide} metalness={0} roughness={0.95} />
    </mesh>
  )
}


// ── Beam Mesh ───────────────────────────────────────────
function BeamMesh({ beam, selected, onSelect }: { beam: ApiBeam; selected?: boolean; onSelect?: (id: string) => void }) {
  const { start, end, width_m, depth_m } = beam
  const color = '#2980b9'

  const { position, rotation, length } = useMemo(() => {
    const dx = end.x - start.x; const dz = end.z - start.z
    const len = Math.sqrt(dx * dx + dz * dz)
    return {
      position: [(start.x + end.x) / 2, start.y - depth_m / 2, (start.z + end.z) / 2] as [number, number, number],
      rotation: [0, -Math.atan2(dz, dx), 0] as [number, number, number],
      length: len,
    }
  }, [beam.beam_id])

  return (
    <group>
      <mesh position={position} rotation={rotation} onClick={e => { e.stopPropagation(); onSelect?.(beam.beam_id) }} castShadow>
        <boxGeometry args={[length, depth_m, width_m]} />
        <meshStandardMaterial
          color={selected ? '#5dade2' : color}
          emissive={selected ? color : '#000'}
          emissiveIntensity={selected ? 0.4 : 0.05}
          opacity={0.9} transparent metalness={0.15} roughness={0.7}
        />
      </mesh>
      {/* Beam cross-hatch pattern for visual clarity */}
      <mesh position={position} rotation={rotation}>
        <boxGeometry args={[length + 0.01, depth_m + 0.01, width_m + 0.01]} />
        <meshBasicMaterial color={color} wireframe opacity={selected ? 0.3 : 0.1} transparent />
      </mesh>
      {selected && (
        <Html position={[(start.x+end.x)/2, start.y+0.4, (start.z+end.z)/2]} center style={{ pointerEvents: 'none' }}>
          <div style={tooltipStyle(color)}>
            <div style={{ fontWeight: 800, color: '#5dade2', fontSize: '13px', marginBottom: '5px' }}>🔩 {beam.beam_id}</div>
            <div style={gridStyle}>
              <Row label="Span" value={`${beam.span_m?.toFixed(2)}m`} />
              <Row label="Size" value={`${(width_m*1000).toFixed(0)}×${(depth_m*1000).toFixed(0)}mm`} />
              <Row label="Steel" value={beam.tension_bars || 'N/A'} />
              <Row label="Stirrups" value={beam.stirrup_description || 'N/A'} />
              <Row label="Moment" value={`${beam.max_bending_moment_knm?.toFixed(1)} kN·m`} />
              <Row label="Shear" value={`${beam.max_shear_force_kn?.toFixed(1)} kN`} />
              <Row label="Grade" value={`${beam.concrete_grade} + ${beam.steel_grade}`} />
              <span>Deflection:</span>
              <span style={{ fontWeight: 700, color: beam.deflection_ok ? '#27ae60' : '#e74c3c' }}>
                {beam.deflection_ok ? '✓ OK' : '✗ Excess'}
              </span>
            </div>
          </div>
        </Html>
      )}
    </group>
  )
}

// ── Column Mesh ─────────────────────────────────────────
function ColumnMesh({ column, selected, onSelect }: { column: ApiColumn; selected?: boolean; onSelect?: (id: string) => void }) {
  const color = '#d4a017'
  const p = column.position

  return (
    <group>
      <mesh position={[p.x, p.y, p.z]} onClick={e => { e.stopPropagation(); onSelect?.(column.column_id) }} castShadow>
        <boxGeometry args={[column.width_m, column.height_m, column.depth_m]} />
        <meshStandardMaterial
          color={selected ? '#f1c40f' : color}
          emissive={selected ? color : '#000'}
          emissiveIntensity={selected ? 0.4 : 0.05}
          opacity={0.9} transparent metalness={0.1} roughness={0.75}
        />
      </mesh>
      {selected && (
        <Html position={[p.x, p.y + column.height_m/2 + 0.3, p.z]} center style={{ pointerEvents: 'none' }}>
          <div style={tooltipStyle(color)}>
            <div style={{ fontWeight: 800, color: '#f1c40f', fontSize: '13px', marginBottom: '5px' }}>🏛 {column.column_id}</div>
            <div style={gridStyle}>
              <Row label="Size" value={`${(column.width_m*1000).toFixed(0)}×${(column.depth_m*1000).toFixed(0)}mm`} />
              <Row label="Height" value={`${column.height_m?.toFixed(1)}m`} />
              <Row label="Axial Load" value={`${column.axial_load_kn?.toFixed(0)} kN`} />
              <Row label="Steel" value={column.steel_bars || 'N/A'} />
              <Row label="Ties" value={`8mm @ ${column.tie_spacing_mm}mm c/c`} />
              <span>Utilization:</span>
              <span style={{ fontWeight: 700, color: (column.load_ratio??0) < 0.8 ? '#27ae60' : '#e74c3c' }}>
                {((column.load_ratio??0)*100).toFixed(0)}%
              </span>
            </div>
          </div>
        </Html>
      )}
    </group>
  )
}

// ── Room Label ──────────────────────────────────────────
function RoomLabel({ label, position, area, type }: { label: string; position: { x: number; y: number; z: number }; area: number; type: string }) {
  return (
    <Html position={[position.x, 0.15, position.z]} center>
      <div style={{
        background: 'rgba(10,20,40,0.8)', backdropFilter: 'blur(8px)',
        border: '1px solid rgba(120,160,220,0.25)', padding: '5px 12px',
        borderRadius: '8px', textAlign: 'center', pointerEvents: 'none',
      }}>
        <p style={{ fontSize: '12px', fontWeight: 700, color: '#e8eef7', margin: 0 }}>{label}</p>
        <p style={{ fontSize: '10px', color: '#78a0dc', margin: '2px 0 0' }}>{area.toFixed(1)} m²</p>
      </div>
    </Html>
  )
}

// ── Helpers ──────────────────────────────────────────────
function Row({ label, value }: { label: string; value: string }) {
  return <><span>{label}:</span><span style={{ fontWeight: 700 }}>{value}</span></>
}

function tooltipStyle(accent: string): React.CSSProperties {
  return {
    background: 'rgba(8,16,32,0.95)', border: `1px solid ${accent}40`, borderRadius: '12px',
    padding: '10px 14px', color: 'white', fontSize: '10px', whiteSpace: 'nowrap' as const,
    boxShadow: `0 8px 32px rgba(0,0,0,0.5), 0 0 20px ${accent}20`,
    backdropFilter: 'blur(12px)', minWidth: '180px',
  }
}

const gridStyle: React.CSSProperties = {
  display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px 12px',
  fontSize: '10px', color: 'rgba(255,255,255,0.8)',
}

function FilterBtn({ label, active, color, onClick }: { label: string; active: boolean; color: string; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: 5, padding: '5px 12px', borderRadius: 6,
      fontSize: 11, fontWeight: 600, cursor: 'pointer',
      border: active ? `1.5px solid ${color}88` : '1.5px solid rgba(255,255,255,0.12)',
      background: active ? `${color}18` : 'rgba(255,255,255,0.04)',
      color: active ? color : 'rgba(255,255,255,0.45)', transition: 'all 0.2s',
    }}>
      <div style={{ width: 8, height: 8, borderRadius: 3, background: active ? color : 'rgba(255,255,255,0.15)' }} />
      {label}
    </button>
  )
}


// ── Scene Content ───────────────────────────────────────
function SceneContent({ sceneGraph, selectedId, onSelect, filters }: {
  sceneGraph: SceneGraph; selectedId?: string; onSelect?: (id: string) => void; filters: ViewerFilters
}) {
  const sg = sceneGraph as any
  const walls: ApiWall[] = sg.walls ?? []
  const beams: ApiBeam[] = sg.beams ?? []
  const columns: ApiColumn[] = sg.columns ?? []
  const slabs: ApiSlab[] = sg.slabs ?? []
  const roomLabels: any[] = sg.room_labels ?? []
  const bounds = sg.camera_bounds ?? {}

  const minX = bounds.min?.x ?? 0; const maxX = bounds.max?.x ?? 10
  const minZ = bounds.min?.z ?? 0; const maxZ = bounds.max?.z ?? 10
  const sizeX = maxX - minX; const sizeZ = maxZ - minZ
  const cx = (minX + maxX) / 2; const cz = (minZ + maxZ) / 2
  const gridSize = Math.max(sizeX, sizeZ) + 6

  return (
    <>
      <ambientLight intensity={0.45} />
      <directionalLight position={[cx + 15, 25, cz + 10]} intensity={0.8} castShadow
        shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
      <directionalLight position={[cx - 10, 18, cz - 15]} intensity={0.35} color="#b0c4de" />
      <hemisphereLight color="#b1e1ff" groundColor="#0a1628" intensity={0.3} />

      {/* Ground plane with grid */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[cx, -0.02, cz]} receiveShadow>
        <planeGeometry args={[gridSize + 4, gridSize + 4]} />
        <meshStandardMaterial color="#0c1a2e" metalness={0} roughness={1} />
      </mesh>
      <gridHelper args={[gridSize, Math.max(10, Math.floor(gridSize)), '#1e3a5f', '#111d33']} position={[cx, 0, cz]} />

      {/* Floor slabs */}
      {filters.showSlabs && slabs.map((slab, i) => <SlabMesh key={slab.id ?? i} slab={slab} />)}

      {/* Walls */}
      {filters.showWalls && walls.map((w, i) => (
        <WallMesh key={w.wall_id ?? i} wall={w} selected={w.wall_id === selectedId} onSelect={onSelect} />
      ))}

      {/* Beams */}
      {filters.showBeams && beams.map((b, i) => (
        <BeamMesh key={b.beam_id ?? i} beam={b} selected={b.beam_id === selectedId} onSelect={onSelect} />
      ))}

      {/* Columns */}
      {filters.showColumns && columns.map((c, i) => (
        <ColumnMesh key={c.column_id ?? i} column={c} selected={c.column_id === selectedId} onSelect={onSelect} />
      ))}

      {/* Room Labels */}
      {filters.showLabels && roomLabels.map((l: any, i: number) => (
        <RoomLabel key={l.room_id ?? i} label={l.label ?? 'Room'} type={l.room_type ?? 'other'}
          position={l.position ?? { x: 0, y: 0, z: 0 }} area={l.area_m2 ?? 0} />
      ))}
    </>
  )
}


// ── Main Viewer ─────────────────────────────────────────
interface ThreeViewerProps {
  sceneGraph: SceneGraph; selectedWallId?: string; onWallSelect?: (id: string) => void; className?: string
}

export function ThreeViewer({ sceneGraph, selectedWallId, onWallSelect, className }: ThreeViewerProps) {
  const sg = sceneGraph as any
  const bounds = sg.camera_bounds ?? {}
  const cx = bounds.center?.x ?? 5; const cz = bounds.center?.z ?? 5
  const dist = Math.max((bounds.max?.x ?? 10) - (bounds.min?.x ?? 0), (bounds.max?.z ?? 10) - (bounds.min?.z ?? 0)) * 0.85

  const [filters, setFilters] = useState<ViewerFilters>({
    showWalls: true, showBeams: true, showColumns: true, showSlabs: true, showLabels: true,
  })
  const [selectedId, setSelectedId] = useState<string | undefined>(selectedWallId)

  const handleSelect = useCallback((id: string) => { setSelectedId(id); onWallSelect?.(id) }, [onWallSelect])

  const beam_n = (sg.beams ?? []).length; const col_n = (sg.columns ?? []).length

  return (
    <div className={className} style={{ background: '#060e1a', position: 'relative' }}>
      <Canvas shadows gl={{ antialias: true, alpha: false, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.2 }}>
        <PerspectiveCamera makeDefault position={[cx + dist * 0.6, dist * 0.7, cz + dist * 0.8]} fov={45} near={0.1} far={1000} />
        <OrbitControls target={[cx, 1.2, cz]} maxPolarAngle={Math.PI / 2 - 0.05} minDistance={2} maxDistance={dist * 4} enablePan enableDamping dampingFactor={0.1} />
        <SceneContent sceneGraph={sceneGraph} selectedId={selectedId} onSelect={handleSelect} filters={filters} />
      </Canvas>

      {/* Info */}
      <div style={{ position: 'absolute', top: 10, left: 12, fontSize: '10px', color: 'rgba(255,255,255,0.4)', zIndex: 10, pointerEvents: 'none' }}>
        3D View — Click element to inspect · Scroll to zoom · Drag to rotate
      </div>

      {/* Filters */}
      <div style={{ position: 'absolute', bottom: 12, left: 12, display: 'flex', gap: 6, flexWrap: 'wrap', zIndex: 10 }}>
        <FilterBtn label="Walls" active={filters.showWalls} color="#c0392b" onClick={() => setFilters(f => ({ ...f, showWalls: !f.showWalls }))} />
        <FilterBtn label={`Beams (${beam_n})`} active={filters.showBeams} color="#2980b9" onClick={() => setFilters(f => ({ ...f, showBeams: !f.showBeams }))} />
        <FilterBtn label={`Columns (${col_n})`} active={filters.showColumns} color="#d4a017" onClick={() => setFilters(f => ({ ...f, showColumns: !f.showColumns }))} />
        <FilterBtn label="Slabs" active={filters.showSlabs} color="#1a2a4a" onClick={() => setFilters(f => ({ ...f, showSlabs: !f.showSlabs }))} />
        <FilterBtn label="Labels" active={filters.showLabels} color="#78a0dc" onClick={() => setFilters(f => ({ ...f, showLabels: !f.showLabels }))} />
      </div>

      {/* Legend */}
      <div style={{
        position: 'absolute', top: 10, right: 12, background: 'rgba(8,16,32,0.85)',
        backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 8, padding: '8px 14px', fontSize: 10, display: 'flex', flexDirection: 'column', gap: 5, zIndex: 10,
      }}>
        {[
          { c: '#c0392b', l: 'Load Bearing Wall' }, { c: '#e67e22', l: 'Structural Spine' },
          { c: '#7fb3d8', l: 'Partition Wall' }, { c: '#8d6e63', l: 'Exterior Wall' },
          { c: '#2980b9', l: 'RCC Beam (IS 456)' }, { c: '#d4a017', l: 'RCC Column' },
        ].map(i => (
          <div key={i.l} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: i.c, border: '1px solid rgba(255,255,255,0.1)' }} />
            <span style={{ color: 'rgba(255,255,255,0.65)' }}>{i.l}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ThreeViewerPlaceholder({ className }: { className?: string }) {
  return (
    <div className={className} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#060e1a' }}>
      <div style={{ textAlign: 'center', color: 'var(--color-muted-foreground)' }}>
        <div style={{ width: 52, height: 52, border: '2px solid rgba(41,128,185,0.3)', borderRadius: 14, margin: '0 auto 14px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: '1.6rem' }}>🏗</span>
        </div>
        <p style={{ fontSize: '0.95rem', fontWeight: 600 }}>3D Structural View</p>
        <p style={{ fontSize: '0.8rem', marginTop: 5, opacity: 0.6 }}>Upload floor plan to visualize structure</p>
      </div>
    </div>
  )
}
