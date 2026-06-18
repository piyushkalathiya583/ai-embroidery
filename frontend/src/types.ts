// Mirrors backend app/schemas.py

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  subscription_tier: string;
  credits: number;
}

export interface Project {
  id: number;
  name: string;
  status: string;
  is_favourite: boolean;
  garment: string | null;
  placement: string | null;
  created_at: string;
  sketch_count: number;
  thumbnail_url: string | null;
}

export interface VisionResult {
  style: string;
  symmetry: boolean;
  density: string;
  motifs: string[];
  border: string;
  layout: string;
}

export interface MeasurementInput {
  waist: number;
  height: number;
  margin: number;
  kali: number;
}

export interface MeasurementResult {
  top_width: number;
  bottom_width: number;
  height: number;
  safe_area: number;
}

export interface Sketch {
  id: number;
  image_path: string;
  image_url: string;
  variant_index: number;
  created_at: string;
}

export interface PipelineResult {
  reference_analysis: VisionResult;
  garment: { garment: string; placement: string };
  measurements: MeasurementResult;
  composition: Record<string, unknown>;
  rules: string[];
  prompt: string;
  output: Sketch[];
}

export interface CollectionItem {
  id: number;
  piece: string;
  image_url: string;
  created_at: string;
}

export interface Collection {
  id: number;
  base_sketch_id: number;
  created_at: string;
  items: CollectionItem[];
}

export interface ProjectState {
  project: Project;
  vision: VisionResult | null;
  measurement_input: MeasurementInput | null;
  measurement_result: MeasurementResult | null;
  sketches: Sketch[];
}

export const GARMENTS = ["Lehenga", "Kurti", "Blouse", "Dupatta", "Panel"];
export const PLACEMENTS = [
  "Single Kali",
  "12 Kali",
  "16 Kali",
  "24 Kali",
  "All Over",
  "Neck",
  "Sleeve",
  "Daman",
  "Border",
  "Panel",
];
export const VARIATIONS = [
  "More Luxury",
  "More Floral",
  "More Empty",
  "Heavy Border",
  "Simple Border",
  "Heavy Fill",
  "Minimal Fill",
];
