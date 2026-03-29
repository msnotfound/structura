import { useRef, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Html } from '@react-three/drei'
import type { SceneGraph, WallClassification } from '@/types'
import * as THREE from 'three'

const WALL_COLORS: Record<WallClassification, string> = {
  load_bearing: '#dc2626',
  partition: '#22c55e',
  structural_spine: '#f59e0b',
}

// API wall shape: { wall_id, vertices_3d: [{x,y,z}], faces: [{vertices:[i,i,i]}], classification, ... }
type ApiWall = {
  wall_id: string
  vertices_3d?: { x: number; y: number; z: number }[]
  vertices?: { x: number; y: number; z: number }[]
  faces?: { vertices: number[] }[]
  classification: WallClassification
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
        // API coords: x=width, y=height(0-2.8m), z=depth(pixels)
        // Scale pixel coords to meters (approx 60px/m based on data)
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

  return (
    <mesh
      ref={meshRef}
      geometry={geometry}
      onClick={() => onSelect?.(wallId)}
    >
      <meshStandardMaterial
        color={color}
        opacity={selected ? 1 : 0.85}
        transparent
        side={THREE.DoubleSide}
      />
      {selected && (
        <lineSegments>
          <edgesGeometry args={[geometry]} />
          <lineBasicMaterial color="#000" />
        </lineSegments>
      )}
    </mesh>
  )
}

interface RoomLabelProps {
  label: string
  position: { x: number; y: number; z: number }
  area: number
}

function RoomLabel({ label, position, area }: RoomLabelProps) {
  return (
    <Html position={[position.x / 60, position.y + 0.5, position.z / 60]} center>
      <div className="bg-white/90 backdrop-blur-sm px-2 py-1 rounded shadow-md text-center pointer-events-none" style={{ whiteSpace: 'nowrap' }}>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        <p className="text-xs text-gray-500">{area.toFixed(1)} m²</p>
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
      <ambientLight intensity={0.6} />
      <directionalLight position={[centerX + 20, 30, centerZ + 10]} intensity={0.8} castShadow />
      <directionalLight position={[centerX - 10, 20, centerZ - 10]} intensity={0.4} />

      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[centerX, -0.01, centerZ]}>
        <planeGeometry args={[sizeX + 4, sizeZ + 4]} />
        <meshStandardMaterial color="#f1f5f9" side={THREE.DoubleSide} />
      </mesh>

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
          label={label.label ?? label.name ?? 'Room'}
          position={label.position ?? { x: 0, y: 1.5, z: 0 }}
          area={label.area_m2 ?? label.area ?? 0}
        />
      ))}

      {/* Grid */}
      <gridHelper
        args={[Math.max(sizeX, sizeZ) + 10, 20, '#ccc', '#eee']}
        position={[centerX, 0, centerZ]}
      />
    </>
  )
}

interface ThreeViewerProps {
  sceneGraph: SceneGraph
  selectedWallId?: string
  onWallSelect?: (id: string) => void
  className?: string
}

export function ThreeViewer({
  sceneGraph,
  selectedWallId,
  onWallSelect,
  className
}: ThreeViewerProps) {
  const sg = sceneGraph as any
  const bounds = sg.camera_bounds ?? {}
  const centerX = ((bounds.center?.x ?? 400) / 60)
  const centerZ = ((bounds.center?.z ?? 300) / 60)
  const dist = Math.max(
    ((bounds.max?.x ?? 800) - (bounds.min?.x ?? 0)) / 60,
    ((bounds.max?.z ?? 600) - (bounds.min?.z ?? 0)) / 60
  ) * 0.8

  return (
    <div className={className}>
      <Canvas shadows>
        <PerspectiveCamera
          makeDefault
          position={[centerX, dist * 0.7, centerZ + dist]}
          fov={50}
        />
        <OrbitControls
          target={[centerX, 1.5, centerZ]}
          maxPolarAngle={Math.PI / 2 - 0.05}
          minDistance={3}
          maxDistance={dist * 3}
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
    <div className={`${className} flex items-center justify-center bg-muted/50 rounded-lg`}>
      <div className="text-center text-muted-foreground">
        <p className="text-lg font-medium">3D Viewer</p>
        <p className="text-sm">Upload a floor plan to see the 3D model</p>
      </div>
    </div>
  )
}
