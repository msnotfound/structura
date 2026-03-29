import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Text, Html } from '@react-three/drei'
import type { SceneGraph, ExtrudedWall, WallClassification } from '@/types'
import * as THREE from 'three'

const WALL_COLORS: Record<WallClassification, string> = {
  load_bearing: '#dc2626',
  partition: '#22c55e',
  structural_spine: '#f59e0b',
}

interface WallMeshProps {
  wall: ExtrudedWall
  selected?: boolean
  onSelect?: (id: string) => void
}

function WallMesh({ wall, selected, onSelect }: WallMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const color = WALL_COLORS[wall.classification]

  // Create geometry from vertices and faces
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    
    // Flatten vertices
    const positions: number[] = []
    wall.vertices.forEach(v => {
      positions.push(v.x, v.z, -v.y) // Swap Y/Z for Three.js coordinate system
    })
    
    // Flatten face indices
    const indices: number[] = []
    wall.faces.forEach(face => {
      indices.push(...face.vertices)
    })
    
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
    geo.setIndex(indices)
    geo.computeVertexNormals()
    
    return geo
  }, [wall])

  return (
    <mesh
      ref={meshRef}
      geometry={geometry}
      onClick={() => onSelect?.(wall.id)}
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
          <lineBasicMaterial color="#000" linewidth={2} />
        </lineSegments>
      )}
    </mesh>
  )
}

interface RoomLabelProps {
  name: string
  position: [number, number, number]
  area: number
}

function RoomLabel({ name, position, area }: RoomLabelProps) {
  return (
    <Html position={position} center>
      <div className="bg-white/90 backdrop-blur-sm px-2 py-1 rounded shadow-md text-center pointer-events-none">
        <p className="text-sm font-medium text-gray-900">{name}</p>
        <p className="text-xs text-gray-500">{area.toFixed(1)} m²</p>
      </div>
    </Html>
  )
}

interface FloorPlaneProps {
  size: [number, number]
}

function FloorPlane({ size }: FloorPlaneProps) {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[size[0] / 2, 0, -size[1] / 2]}>
      <planeGeometry args={size} />
      <meshStandardMaterial color="#f1f5f9" side={THREE.DoubleSide} />
    </mesh>
  )
}

interface SceneContentProps {
  sceneGraph: SceneGraph
  selectedWallId?: string
  onWallSelect?: (id: string) => void
}

function SceneContent({ sceneGraph, selectedWallId, onWallSelect }: SceneContentProps) {
  const { camera_bounds } = sceneGraph

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 20, 10]} intensity={0.8} castShadow />
      <directionalLight position={[-10, 20, -10]} intensity={0.4} />

      {/* Floor */}
      <FloorPlane size={[
        camera_bounds.max.x - camera_bounds.min.x + 2,
        camera_bounds.max.y - camera_bounds.min.y + 2
      ]} />

      {/* Walls */}
      {sceneGraph.walls.map(wall => (
        <WallMesh
          key={wall.id}
          wall={wall}
          selected={wall.id === selectedWallId}
          onSelect={onWallSelect}
        />
      ))}

      {/* Room Labels */}
      {sceneGraph.room_labels.map(label => (
        <RoomLabel
          key={label.room_id}
          name={label.name}
          position={[label.position.x, label.position.z + 0.5, -label.position.y]}
          area={label.area}
        />
      ))}

      {/* Grid Helper */}
      <gridHelper args={[50, 50, '#ccc', '#eee']} position={[0, 0.01, 0]} />
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
  const { camera_bounds } = sceneGraph

  return (
    <div className={className}>
      <Canvas shadows>
        <PerspectiveCamera
          makeDefault
          position={[
            camera_bounds.center.x + camera_bounds.recommended_distance,
            camera_bounds.recommended_distance * 0.8,
            -camera_bounds.center.y + camera_bounds.recommended_distance
          ]}
          fov={50}
        />
        <OrbitControls
          target={[camera_bounds.center.x, 1.5, -camera_bounds.center.y]}
          maxPolarAngle={Math.PI / 2 - 0.1}
          minDistance={5}
          maxDistance={100}
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

// Placeholder for when no scene is loaded
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
