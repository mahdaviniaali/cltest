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
  section_key: string;
  brand: string | null;
  model: string | null;
  brand_term_id: number | null;
  model_term_id: number | null;
  min_year: number | null;
  max_price: number | null;
  max_mileage: number | null;
  location: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  bootstrapped_at?: string | null;
  last_bootstrap_job_id?: string | null;
}

export interface SearchCreateResponse extends Search {
  cached_count: number;
  cache_sufficient: boolean;
  is_crawling: boolean;
  job_id?: string | null;
}

export interface SearchInput {
  name?: string;
  section_key?: string;
  brand?: string;
  model?: string;
  brand_term_id?: number;
  model_term_id?: number;
  min_year?: number;
  max_price?: number;
  max_mileage?: number;
  location?: string;
  enabled?: boolean;
}

/** PUT /api/searches/{id} — send null to clear a stored criterion. */
export interface SearchUpdateInput {
  name?: string | null;
  section_key?: string | null;
  brand?: string | null;
  model?: string | null;
  brand_term_id?: number | null;
  model_term_id?: number | null;
  min_year?: number | null;
  max_price?: number | null;
  max_mileage?: number | null;
  location?: string | null;
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
  bootstrapped?: boolean;
  cache_sufficient?: boolean;
}

export interface DataStatus {
  last_updated_at: string | null;
  is_refreshing: boolean;
}

export interface RefreshResponse {
  is_refreshing: boolean;
  message: string;
  job_id?: string | null;
  used_bootstrap?: boolean;
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
