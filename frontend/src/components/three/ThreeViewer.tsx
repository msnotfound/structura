import { useRef, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Html } from '@react-three/drei'
import type { SceneGraph, WallClassification } from '@/types'
import * as THREE from 'three'

const WALL_COLORS: Record<WallClassification, string> = {
  load_bearing:     '#ef4444',  // vivid red
  partition:        '#22d3ee',  // cyan
  structural_spine: '#f59e0b',  // amber
}

const WALL_LABELS: Record<WallClassification, string> = {
  load_bearing:     'Load Bearing',
  partition:        'Partition',
  structural_spine: 'Structural Spine',
}

// API wall shape: { wall_id, vertices_3d: [{x,y,z}], faces: [{vertices:[i,i,i]}], classification }
type ApiWall = {
  wall_id: string
  vertices_3d?: { x: number; y: number; z: number }[]
  vertices?: { x: number; y: number; z: number }[]
  faces?: { vertices: number[] }[]
  classification: WallClassification
  length_m?: number
  color?: string
}

interface WallMeshProps {
  wall: ApiWall
  selected?: boolean
  onSelect?: (id: string) => void
}

function WallMesh({ wall, selected, onSelect }: WallMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const color = WALL_COLORS[wall.classification] ?? '#888888'
  const verts = wall.vertices_3d ?? wall.vertices ?? []
  const faces = wall.faces ?? []

  const geometry = useMemo(() => {
    if (!verts.length || !faces.length) return null
    try {
      const geo = new THREE.BufferGeometry()
      const positions: number[] = []
      verts.forEach(v => {
        // Scale pixel → meters (~60px/m)
        positions.push(v.x / 60, v.y, v.z / 60)
      })
      const indices: number[] = []
      faces.forEach(face => {
        if (face.vertices?.length >= 3) {
          indices.push(...face.vertices)
        }
      })
      geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
      geo.setIndex(indices)
      geo.computeVertexNormals()
      return geo
    } catch {
      return null
    }
  }, [wall.wall_id])

  if (!geometry) return null

  const wallId = wall.wall_id

  // Calculate center of wall for popup position
  const centerPos = useMemo(() => {
    if (!verts.length) return [0, 2.5, 0] as [number, number, number]
    const avgX = verts.reduce((s, v) => s + v.x, 0) / verts.length
    const avgY = verts.reduce((s, v) => s + v.y, 0) / verts.length
    const avgZ = verts.reduce((s, v) => s + v.z, 0) / verts.length
    return [avgX / 60, avgY + 0.5, avgZ / 60] as [number, number, number]
  }, [wall.wall_id])

  return (
    <group>
      <mesh
        ref={meshRef}
        geometry={geometry}
        onClick={(e) => { e.stopPropagation(); onSelect?.(wallId) }}
      >
        <meshStandardMaterial
          color={color}
          emissive={selected ? color : '#000000'}
          emissiveIntensity={selected ? 0.4 : 0}
          opacity={selected ? 1 : 0.78}
          transparent
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Edge highlight when selected */}
      {selected && (
        <lineSegments geometry={new THREE.EdgesGeometry(geometry)}>
          <lineBasicMaterial color={color} linewidth={2} />
        </lineSegments>
      )}

      {/* Info popup when selected */}
      {selected && (
        <Html position={centerPos} center style={{ pointerEvents: 'none' }}>
          <div style={{
            background: 'rgba(5,13,26,0.92)',
            border: `1px solid ${color}55`,
            borderRadius: '10px',
            padding: '8px 12px',
            color: 'white',
            fontSize: '11px',
            whiteSpace: 'nowrap',
            boxShadow: `0 4px 20px rgba(0,0,0,0.5), 0 0 12px ${color}30`,
            backdropFilter: 'blur(10px)',
            minWidth: '120px',
          }}>
            <div style={{ fontFamily: 'monospace', fontWeight: 800, color, marginBottom: '4px', fontSize: '12px' }}>{wallId}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'rgba(255,255,255,0.7)' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: color, flexShrink: 0 }} />
              <span>{WALL_LABELS[wall.classification] ?? wall.classification}</span>
            </div>
            {wall.length_m && (
              <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '10px', marginTop: '3px' }}>
                Length: {wall.length_m.toFixed(2)} m
              </div>
            )}
          </div>
        </Html>
      )}
    </group>
  )
}

interface RoomLabelProps {
  label: string
  position: { x: number; y: number; z: number }
  area: number
}

function RoomLabel({ label, position, area }: RoomLabelProps) {
  return (
    <Html position={[position.x / 60, (position.y ?? 0) + 0.3, position.z / 60]} center>
      <div style={{
        background: 'rgba(5,13,26,0.75)',
        backdropFilter: 'blur(8px)',
        border: '1px solid rgba(167,139,250,0.3)',
        padding: '4px 10px',
        borderRadius: '8px',
        textAlign: 'center',
        pointerEvents: 'none',
        whiteSpace: 'nowrap',
      }}>
        <p style={{ fontSize: '11px', fontWeight: 700, color: '#e2eaf7' }}>{label}</p>
        <p style={{ fontSize: '9px', color: '#a78bfa' }}>{area.toFixed(1)} m²</p>
      </div>
    </Html>
  )
}

interface SceneContentProps {
  sceneGraph: SceneGraph
  selectedWallId?: string
  onWallSelect?: (id: string) => void
}

function SceneContent({ sceneGraph, selectedWallId, onWallSelect }: SceneContentProps) {
  const sg = sceneGraph as any
  const walls: ApiWall[] = sg.walls ?? []
  const roomLabels: any[] = sg.room_labels ?? []
  const bounds = sg.camera_bounds ?? {}
  const minX = (bounds.min?.x ?? 0) / 60
  const maxX = (bounds.max?.x ?? 100) / 60
  const minZ = (bounds.min?.z ?? 0) / 60
  const maxZ = (bounds.max?.z ?? 100) / 60
  const sizeX = maxX - minX
  const sizeZ = maxZ - minZ
  const centerX = (minX + maxX) / 2
  const centerZ = (minZ + maxZ) / 2

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[centerX + 20, 30, centerZ + 10]} intensity={0.9} />
      <directionalLight position={[centerX - 10, 20, centerZ - 20]} intensity={0.4} color="#93c5fd" />
      <pointLight position={[centerX, 10, centerZ]} intensity={0.3} color="#22d3ee" />

      {/* Floor — dark premium */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[centerX, -0.01, centerZ]}>
        <planeGeometry args={[sizeX + 4, sizeZ + 4]} />
        <meshStandardMaterial color="#0a1628" side={THREE.DoubleSide} />
      </mesh>

      {/* Floor grid (subtle) */}
      <gridHelper
        args={[Math.max(sizeX, sizeZ) + 10, 20, '#1e3a5f', '#0f2040']}
        position={[centerX, 0, centerZ]}
      />

      {/* Walls */}
      {walls.map((wall, idx) => (
        <WallMesh
          key={wall.wall_id ?? idx}
          wall={wall}
          selected={wall.wall_id === selectedWallId}
          onSelect={onWallSelect}
        />
      ))}

      {/* Room Labels */}
      {roomLabels.map((label: any, idx: number) => (
        <RoomLabel
          key={label.room_id ?? idx}
          label={label.label ?? label.name ?? label.room_label ?? 'Room'}
          position={label.position ?? { x: 0, y: 1.5, z: 0 }}
          area={label.area_m2 ?? label.area ?? 0}
        />
      ))}
    </>
  )
}

interface ThreeViewerProps {
  sceneGraph: SceneGraph
  selectedWallId?: string
  onWallSelect?: (id: string) => void
  className?: string
}

export function ThreeViewer({ sceneGraph, selectedWallId, onWallSelect, className }: ThreeViewerProps) {
  const sg = sceneGraph as any
  const bounds = sg.camera_bounds ?? {}
  const centerX = ((bounds.center?.x ?? 400) / 60)
  const centerZ = ((bounds.center?.z ?? 300) / 60)
  const dist = Math.max(
    ((bounds.max?.x ?? 800) - (bounds.min?.x ?? 0)) / 60,
    ((bounds.max?.z ?? 600) - (bounds.min?.z ?? 0)) / 60
  ) * 0.85

  return (
    <div className={className} style={{ background: '#050d1a' }}>
      <Canvas shadows={false} gl={{ antialias: true, alpha: false }}>
        <PerspectiveCamera
          makeDefault
          position={[centerX, dist * 0.75, centerZ + dist]}
          fov={48}
        />
        <OrbitControls
          target={[centerX, 1.5, centerZ]}
          maxPolarAngle={Math.PI / 2 - 0.05}
          minDistance={3}
          maxDistance={dist * 3}
          enablePan
        />
        <SceneContent
          sceneGraph={sceneGraph}
          selectedWallId={selectedWallId}
          onWallSelect={onWallSelect}
        />
      </Canvas>
    </div>
  )
}

export function ThreeViewerPlaceholder({ className }: { className?: string }) {
  return (
    <div className={className} style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: '#050d1a',
    }}>
      <div style={{ textAlign: 'center', color: 'var(--color-muted-foreground)' }}>
        <div style={{
          width: '48px', height: '48px', border: '2px solid rgba(59,130,246,0.3)',
          borderRadius: '12px', margin: '0 auto 12px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: '1.5rem' }}>🏗</span>
        </div>
        <p style={{ fontSize: '0.9rem', fontWeight: 600 }}>3D Viewer</p>
        <p style={{ fontSize: '0.78rem', marginTop: '4px' }}>Upload a floor plan to see the 3D model</p>
      </div>
    </div>
  )
}
