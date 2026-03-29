// Geometry types
export interface Point2D {
  x: number
  y: number
}

export interface Point3D {
  x: number
  y: number
  z: number
}

// Parsing types
export interface WallSegment {
  id: string
  start: Point2D
  end: Point2D
  thickness: number
  confidence: number
}

export interface Opening {
  id: string
  type: 'door' | 'window'
  position: Point2D
  width: number
  height: number
  wall_id: string | null
  confidence: number
}

export interface Room {
  id: string
  name: string
  type: string
  vertices: Point2D[]
  area: number
  confidence: number
}

export interface ScaleReference {
  pixels_per_meter: number
  reference_dimension: number | null
  confidence: number
}

export interface ParseResult {
  walls: WallSegment[]
  openings: Opening[]
  rooms: Room[]
  scale: ScaleReference
  image_dimensions: { width: number; height: number }
  agreement_score: number
}

// Geometry classification types
export type WallClassification = 'load_bearing' | 'partition' | 'structural_spine'

export interface Junction {
  id: string
  position: Point2D
  connected_wall_ids: string[]
  type: 'L' | 'T' | 'X' | 'end'
}

export interface ClassifiedWall {
  id: string
  start: Point2D
  end: Point2D
  thickness: number
  classification: WallClassification
  confidence: number
  connected_rooms: string[]
  span_length: number
}

export interface GeometryResult {
  classified_walls: ClassifiedWall[]
  junctions: Junction[]
  rooms: Room[]
  structural_spine_ids: string[]
  load_paths: string[][]
}

// Structural types
export interface SpanAnalysis {
  wall_id: string
  span_length: number
  max_recommended_span: number
  is_within_limit: boolean
  support_count: number
}

export type WarningSeverity = 'info' | 'warning' | 'critical'

export interface StructuralWarning {
  id: string
  severity: WarningSeverity
  message: string
  affected_elements: string[]
  recommendation: string
}

export interface StructuralAnalysisResult {
  span_analyses: SpanAnalysis[]
  warnings: StructuralWarning[]
  overall_integrity_score: number
  load_path_valid: boolean
  thickness_adequate: boolean
}

// 3D Scene types
export interface Face {
  vertices: number[]
  normal: Point3D
}

export interface ExtrudedWall {
  id: string
  vertices: Point3D[]
  faces: Face[]
  classification: WallClassification
  height: number
  base_z: number
}

export interface Slab {
  id: string
  vertices: Point3D[]
  faces: Face[]
  thickness: number
  z_position: number
  type: 'floor' | 'ceiling'
}

export interface RoomLabel3D {
  room_id: string
  name: string
  position: Point3D
  area: number
}

export interface CameraBounds {
  min: Point3D
  max: Point3D
  center: Point3D
  recommended_distance: number
}

export interface SceneGraph {
  walls: ExtrudedWall[]
  slabs: Slab[]
  room_labels: RoomLabel3D[]
  openings: Opening[]
  camera_bounds: CameraBounds
  metadata: {
    total_floor_area: number
    wall_count: number
    room_count: number
    floor_height: number
  }
}

// Material types
export interface Material {
  id: string
  name: string
  type: string
  compressive_strength_mpa: number
  thermal_conductivity: number
  fire_rating_hours: number
  cost_per_unit: number
  unit: string
  durability_rating: number
  environmental_score: number
  suitable_for: string[]
  pros: string[]
  cons: string[]
}

export interface MaterialOption {
  material: Material
  suitability_score: number
  cost_estimate: number
  reasoning: string
}

export interface MaterialRecommendation {
  element_id: string
  element_type: string
  recommended_materials: MaterialOption[]
  selected_material_id: string | null
}

export interface MaterialsResult {
  recommendations: MaterialRecommendation[]
  total_estimated_cost: number
  cost_breakdown: {
    category: string
    cost: number
    percentage: number
  }[]
}

// Cost types
export interface CostLineItem {
  description: string
  quantity: number
  unit: string
  unit_cost: number
  total_cost: number
  material_id: string | null
}

export interface RoomCost {
  room_id: string
  room_name: string
  room_type: string
  area: number
  line_items: CostLineItem[]
  subtotal: number
}

export interface CategoryCost {
  category: string
  items: CostLineItem[]
  subtotal: number
  percentage_of_total: number
}

export interface ProjectCost {
  room_costs: RoomCost[]
  category_costs: CategoryCost[]
  subtotal: number
  contingency_percentage: number
  contingency_amount: number
  tax_percentage: number
  tax_amount: number
  grand_total: number
  cost_per_sqft: number
  currency: string
}

export interface CostComparison {
  scenario_name: string
  project_cost: ProjectCost
  savings_vs_baseline: number | null
}

// Report types
export interface ElementExplanation {
  element_id: string
  element_type: string
  classification: string
  explanation: string
  key_factors: string[]
}

export interface OptimizationSuggestion {
  id: string
  title: string
  description: string
  potential_savings: number | null
  impact_level: 'low' | 'medium' | 'high'
  affected_elements: string[]
}

export interface FullReport {
  summary: string
  structural_assessment: string
  element_explanations: ElementExplanation[]
  optimization_suggestions: OptimizationSuggestion[]
  material_rationale: string
  cost_summary: string
  warnings_summary: string
  recommendations: string[]
}

// Analysis result combining all
export interface AnalysisResult {
  file_id: string
  parse_result: ParseResult
  geometry_result: GeometryResult
  structural_result: StructuralAnalysisResult
  materials_result: MaterialsResult
  cost_result: ProjectCost
  report: FullReport
  scene_graph: SceneGraph
}

// API response types
export interface UploadResponse {
  file_id: string
  filename: string
  message: string
}

export interface HealthResponse {
  status: string
  version: string
}
