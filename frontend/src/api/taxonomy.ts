import { request } from "./client";

export interface TaxonomySection {
  section_key: string;
  label: string;
  brand_count: number;
  model_count: number;
  page_count?: number;
}

export interface TaxonomyTerm {
  id: number;
  section_key: string;
  term_type: string;
  parent_id: number | null;
  label: string;
  slug: string;
  listing_url: string | null;
}

export interface TaxonomyCity {
  id: number;
  label: string;
  section_key: string;
}

export const taxonomyApi = {
  sections: () => request<TaxonomySection[]>("/api/taxonomy/sections"),
  brands: (section: string) =>
    request<TaxonomyTerm[]>(`/api/taxonomy/brands?section=${encodeURIComponent(section)}`),
  models: (section: string, brandId: number) =>
    request<TaxonomyTerm[]>(
      `/api/taxonomy/models?section=${encodeURIComponent(section)}&brand_id=${brandId}`,
    ),
  cities: (section: string) =>
    request<TaxonomyCity[]>(`/api/taxonomy/cities?section=${encodeURIComponent(section)}`),
  harvest: () =>
    request<TaxonomyHarvest>(`/api/taxonomy/harvest`, { method: "POST" }),
};

export interface TaxonomyHarvest {
  brands: number;
  models: number;
  snapshot_id: number | null;
  skipped: boolean;
}
