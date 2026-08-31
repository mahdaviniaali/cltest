import type { StatsOverview } from "../../api/inspector";

interface Props {
  overview: StatsOverview | null;
  siteNodeCount: number;
  loading?: boolean;
}

export default function InspectorOverviewBar({ overview, siteNodeCount, loading }: Props) {
  if (loading && !overview) {
    return <div className="inspector-overview muted">در حال بارگذاری خلاصه…</div>;
  }
  if (!overview) return null;

  const { crawl_health: ch, last_site_map_job: last } = overview;
  const siteNodes = overview.table_counts.find((t) => t.table === "site_nodes")?.count ?? siteNodeCount;
  const ads = overview.table_counts.find((t) => t.table === "advertisements")?.count ?? 0;
  const searches = overview.table_counts.find((t) => t.table === "searches")?.count ?? 0;

  return (
    <div className="inspector-overview">
      <div className="overview-chip">
        <span className="overview-label">صفحات سایت</span>
        <strong>{siteNodes.toLocaleString("fa-IR")}</strong>
      </div>
      <div className="overview-chip">
        <span className="overview-label">آگهی‌ها</span>
        <strong>{ads.toLocaleString("fa-IR")}</strong>
      </div>
      <div className="overview-chip">
        <span className="overview-label">فیلترها</span>
        <strong>{searches.toLocaleString("fa-IR")}</strong>
      </div>
      <div className="overview-chip">
        <span className="overview-label">برند / مدل</span>
        <strong>
          {overview.taxonomy_active_brands}/{overview.taxonomy_active_models}
        </strong>
      </div>
      <div className="overview-chip">
        <span className="overview-label">Jobs فعال</span>
        <strong className={ch.running > 0 ? "text-running" : ""}>{ch.running.toLocaleString("fa-IR")}</strong>
      </div>
      <div className="overview-chip">
        <span className="overview-label">Site-map</span>
        <strong>{last.status ?? "—"}</strong>
        {last.pages_crawled > 0 && (
          <small>
            {last.pages_crawled}/{last.pages_discovered}
          </small>
        )}
      </div>
    </div>
  );
}
