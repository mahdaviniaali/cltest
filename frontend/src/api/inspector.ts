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
};
