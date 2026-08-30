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
