import { request } from "./client";

export interface SiteMapJob {
  job_id: string;
  status: string;
  job_type: string;
  pages_crawled: number;
  pages_discovered: number;
  pages_failed: number;
  current_depth: number;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
}

export interface CrawlEvent {
  id: number;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface SiteTreeNode {
  path: string;
  label: string;
  page_key?: string | null;
  url?: string | null;
  page_type?: string | null;
  section?: string | null;
  children: SiteTreeNode[];
}

export interface SiteNodeSummary {
  page_key: string;
  url: string;
  url_pattern: string;
  depth: number;
  page_type: string;
  section?: string | null;
  title?: string | null;
  status: string;
}

export interface SiteGraph {
  nodes: SiteNodeSummary[];
  edges: Array<{ from: string; to: string; type: string }>;
}

export interface SiteMapGroupNode {
  group_key: string;
  parent_group_key?: string | null;
  group_kind: string;
  label: string;
  section?: string | null;
  path_prefix?: string | null;
  url_pattern?: string | null;
  page_type?: string | null;
  page_count: number;
  weight: number;
  inbound_link_count: number;
  representative_page_key?: string | null;
  representative_url?: string | null;
  depth: number;
}

export interface SiteMap {
  nodes: SiteMapGroupNode[];
  edges: Array<{ from: string; to: string; type: string }>;
}

export interface SiteSection {
  section_key: string;
  label: string;
  root_urls: string[];
  url_patterns: string[];
  page_count: number;
  useful_score: number;
}

export interface SitePageDetail {
  page_key: string;
  url: string;
  url_pattern: string;
  depth: number;
  parent_page_key?: string | null;
  page_type: string;
  section?: string | null;
  title?: string | null;
  excerpt?: string | null;
  status: string;
  meta?: Record<string, unknown> | null;
  outbound_links: Array<{ page_key: string; url: string; relation_type: string }>;
}

export interface StatsOverview {
  table_counts: Array<{ table: string; count: number }>;
  site_coverage: Array<{ section: string; page_type: string; count: number }>;
  depth_distribution: Array<{ depth: number; count: number }>;
  taxonomy_active_brands: number;
  taxonomy_active_models: number;
  taxonomy_stale_terms: number;
  last_site_map_job: {
    job_id?: string | null;
    status?: string | null;
    pages_crawled: number;
    pages_discovered: number;
    pages_failed: number;
    started_at?: string | null;
    finished_at?: string | null;
  };
  crawl_health: {
    total_jobs: number;
    completed: number;
    failed: number;
    running: number;
    site_map_jobs: number;
    avg_pages_discovered: number;
    avg_pages_crawled: number;
  };
}

export interface SearchDiscoveryStat {
  search_id: number;
  name?: string | null;
  brand?: string | null;
  model?: string | null;
  section_key: string;
  enabled: boolean;
  bootstrapped_at?: string | null;
  listing_url?: string | null;
  pages_crawled: number;
  ads_found: number;
  matching_count: number;
  match_rate?: number | null;
  low_yield: boolean;
  metric_at?: string | null;
}

export interface FilterCrawlStat {
  fingerprint: string;
  section_key: string;
  listing_url: string;
  brand?: string | null;
  model?: string | null;
  min_year?: number | null;
  max_price?: number | null;
  max_mileage?: number | null;
  location?: string | null;
  last_seen_bama_id?: string | null;
  last_crawl_at?: string | null;
  last_job_id?: string | null;
  enabled_search_count: number;
  active_job_id?: string | null;
  active_job_status?: string | null;
}

export interface HealthReady {
  status: string;
  checks: Record<string, string>;
}

export interface CrawlJobSummary {
  id: string;
  job_type: string;
  status: string;
  triggered_by: string;
  search_id?: number | null;
  pages_crawled: number;
  ads_found: number;
  ads_new: number;
  error?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at: string;
}

export interface CrawlStatus {
  last_seen_bama_id?: string | null;
  last_crawl_at?: string | null;
  last_run_job_id?: string | null;
  latest_job?: CrawlJobSummary | null;
  is_refreshing: boolean;
  last_updated_at?: string | null;
}

export const inspectorApi = {
  startSiteMap(maxPages?: number, maxDepth?: number) {
    return request<SiteMapJob>("/api/inspector/site-map/start", {
      method: "POST",
      body: JSON.stringify({ max_pages: maxPages, max_depth: maxDepth }),
    });
  },
  listJobs() {
    return request<SiteMapJob[]>("/api/inspector/jobs");
  },
  getJob(jobId: string) {
    return request<SiteMapJob>(`/api/inspector/jobs/${jobId}`);
  },
  pauseJob(jobId: string) {
    return request<SiteMapJob>(`/api/inspector/jobs/${jobId}/pause`, { method: "POST" });
  },
  resumeJob(jobId: string) {
    return request<SiteMapJob>(`/api/inspector/jobs/${jobId}/resume`, { method: "POST" });
  },
  cancelJob(jobId: string) {
    return request<SiteMapJob>(`/api/inspector/jobs/${jobId}/cancel`, { method: "POST" });
  },
  listEvents(jobId: string, sinceId = 0) {
    return request<CrawlEvent[]>(`/api/inspector/jobs/${jobId}/events?since_id=${sinceId}`);
  },
  getTree(section?: string) {
    const q = section ? `?section=${encodeURIComponent(section)}` : "";
    return request<SiteTreeNode[]>(`/api/inspector/site/tree${q}`);
  },
  getMap(section?: string) {
    const q = section ? `?section=${encodeURIComponent(section)}` : "";
    return request<SiteMap>(`/api/inspector/site/map${q}`);
  },
  getSections() {
    return request<SiteSection[]>("/api/inspector/site/sections");
  },
  getPage(pageKey: string) {
    return request<SitePageDetail>(`/api/inspector/pages/${pageKey}`);
  },
  getStatsOverview() {
    return request<StatsOverview>("/api/inspector/stats/overview");
  },
  getStatsSearches(threshold = 5) {
    return request<SearchDiscoveryStat[]>(`/api/inspector/stats/searches?threshold=${threshold}`);
  },
  getFilterCrawls() {
    return request<FilterCrawlStat[]>("/api/admin/filter-crawls");
  },
  async getHealthReady() {
    const token = localStorage.getItem("bama_token");
    const headers = new Headers({ "Content-Type": "application/json" });
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch("/api/health/ready", { headers });
    return (await response.json()) as HealthReady;
  },
  async getCrawlStatus() {
    const [status, dataStatus] = await Promise.all([
      request<Omit<CrawlStatus, "is_refreshing" | "last_updated_at">>("/api/crawl/status"),
      request<{ last_updated_at?: string | null; is_refreshing: boolean }>("/api/data/status"),
    ]);
    return {
      ...status,
      is_refreshing: dataStatus.is_refreshing,
      last_updated_at: dataStatus.last_updated_at,
    } satisfies CrawlStatus;
  },
};
