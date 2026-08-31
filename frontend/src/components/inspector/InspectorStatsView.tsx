import { useEffect, useState } from "react";
import { inspectorApi, type SearchDiscoveryStat, type StatsOverview } from "../api/inspector";

export default function InspectorStatsView() {
  const [overview, setOverview] = useState<StatsOverview | null>(null);
  const [searches, setSearches] = useState<SearchDiscoveryStat[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void Promise.all([inspectorApi.getStatsOverview(), inspectorApi.getStatsSearches()])
      .then(([ov, sr]) => {
        setOverview(ov);
        setSearches(sr);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "خطا در بارگذاری آمار"));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!overview) return <p className="muted">در حال بارگذاری آمار…</p>;

  const lowYield = searches.filter((s) => s.low_yield);

  return (
    <div className="inspector-stats-panel">
      <div className="inspector-stats-cards">
        <div className="stat-card">
          <span className="stat-label">برند فعال</span>
          <strong>{overview.taxonomy_active_brands}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">مدل فعال</span>
          <strong>{overview.taxonomy_active_models}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">اصطلاح stale</span>
          <strong>{overview.taxonomy_stale_terms}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">کرawl jobs</span>
          <strong>
            {overview.crawl_health.completed}/{overview.crawl_health.total_jobs}
          </strong>
        </div>
      </div>

      {overview.last_site_map_job.job_id && (
        <section className="panel">
          <h3>آخرین site-map</h3>
          <p className="muted">
            {overview.last_site_map_job.status} — crawled {overview.last_site_map_job.pages_crawled} / discovered{" "}
            {overview.last_site_map_job.pages_discovered}
          </p>
        </section>
      )}

      <section className="panel">
        <h3>فیلترهای کم‌بازده ({lowYield.length})</h3>
        {lowYield.length === 0 ? (
          <p className="muted">همه فیلترها نتیجه کافی دارند.</p>
        ) : (
          <table className="stats-table">
            <thead>
              <tr>
                <th>فیلتر</th>
                <th>URL</th>
                <th>match</th>
                <th>ads</th>
              </tr>
            </thead>
            <tbody>
              {lowYield.map((row) => (
                <tr key={row.search_id}>
                  <td>
                    #{row.search_id} {[row.brand, row.model].filter(Boolean).join(" ") || row.name || "—"}
                  </td>
                  <td className="mono">{row.listing_url ?? "—"}</td>
                  <td>{row.matching_count}</td>
                  <td>{row.ads_found}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel">
        <h3>پوشش سایت (نمونه)</h3>
        <table className="stats-table">
          <thead>
            <tr>
              <th>بخش</th>
              <th>نوع</th>
              <th>تعداد</th>
            </tr>
          </thead>
          <tbody>
            {overview.site_coverage.slice(0, 12).map((row, i) => (
              <tr key={`${row.section}-${row.page_type}-${i}`}>
                <td>{row.section}</td>
                <td>{row.page_type}</td>
                <td>{row.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
