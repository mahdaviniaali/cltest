export interface User {
  id: number;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface Search {
  id: number;
  user_id: number;
  name: string | null;
  brand: string | null;
  model: string | null;
  min_year: number | null;
  max_price: number | null;
  max_mileage: number | null;
  location: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface SearchInput {
  name?: string;
  brand?: string;
  model?: string;
  min_year?: number;
  max_price?: number;
  max_mileage?: number;
  location?: string;
  enabled?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Ad {
  id: number;
  bama_id: string;
  url: string;
  title: string;
  brand: string | null;
  model: string | null;
  year: number | null;
  price: number | null;
  mileage: number | null;
  location: string | null;
  crawled_at: string;
}

export interface DataPreview {
  ads: Ad[];
  total_count: number;
  last_updated_at: string | null;
  is_refreshing: boolean;
}

export interface DataStatus {
  last_updated_at: string | null;
  is_refreshing: boolean;
}

export interface RefreshResponse {
  is_refreshing: boolean;
  message: string;
}

export interface AdFilterInput {
  brand?: string;
  model?: string;
  min_year?: number;
  max_price?: number;
  max_mileage?: number;
  location?: string;
  limit?: number;
}
