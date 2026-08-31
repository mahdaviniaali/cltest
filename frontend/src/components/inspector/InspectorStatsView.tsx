import { useCallback, useEffect, useState } from "react";
import { inspectorApi, type FilterCrawlStat, type SearchDiscoveryStat, type StatsOverview } from "../../api/inspector";

type SearchFilter = "all" | "low_yield" | "enabled" | "disabled";

function fmtTime(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("fa-IR");
}

function fmtPct(value?: number | null) {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
}

export default function InspectorStatsView() {
  const [overview, setOverview] = useState<StatsOverview | null>(null);
  const [searches, setSearches] = useState<SearchDiscoveryStat[]>([]);
  const [filterCrawls, setFilterCrawls] = useState<FilterCrawlStat[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState<SearchFilter>("all");
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    const results = await Promise.allSettled([
      inspectorApi.getStatsOverview(),
      inspectorApi.getStatsSearches(),
      inspectorApi.getFilterCrawls(),
    ]);
    const nextErrors: string[] = [];
    if (results[0].status === "fulfilled") setOverview(results[0].value);
    else nextErrors.push(`overview: ${results[0].reason instanceof Error ? results[0].reason.message : "خطا"}`);
    if (results[1].status === "fulfilled") setSearches(results[1].value);
    else nextErrors.push(`searches: ${results[1].reason instanceof Error ? results[1].reason.message : "خطا"}`);
    if (results[2].status === "fulfilled") setFilterCrawls(results[2].value);
    else nextErrors.push(`filter-crawls: ${results[2].reason instanceof Error ? results[2].reason.message : "خطا"}`);
    setErrors(nextErrors);
    setLastRefresh(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 10000);
    return () => window.clearInterval(id);
  }, [refresh]);

  if (loading && !overview) return <p className="muted">در حال بارگذاری آمار…</p>;

  const ch = overview?.crawl_health;
  const filteredSearches = searches.filter((s) => {
    if (searchFilter === "low_yield") return s.low_yield;
    if (searchFilter === "enabled") return s.enabled;
    if (searchFilter === "disabled") return !s.enabled;
    return true;
  });

  return (
    <div className="inspector-stats-panel">
      {errors.length > 0 && (
        <div className="error-banner">
          {errors.map((e) => (
            <p key={e} className="error">
              {e}
            </p>
          ))}
        </div>
      )}

      <div className="stats-toolbar">
        <span className="muted">
          {lastRefresh ? `آخرین بروزرسانی: ${lastRefresh.toLocaleTimeString("fa-IR")}` : ""}
        </span>
        <button type="button" className="secondary refresh-btn" onClick={() => void refresh()}>
          بروزرسانی
        </button>
      </div>

      {overview && (
        <>
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
              <span className="stat-label">Jobs تکمیل</span>
              <strong>
                {ch?.completed ?? 0}/{ch?.total_jobs ?? 0}
              </strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Jobs فعال</span>
              <strong className={ch && ch.running > 0 ? "text-running" : ""}>{ch?.running ?? 0}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Jobs ناموفق</span>
              <strong className={ch && ch.failed > 0 ? "text-failed" : ""}>{ch?.failed ?? 0}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">Site-map jobs</span>
              <strong>{ch?.site_map_jobs ?? 0}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">میانگین کشف</span>
              <strong>{Math.round(ch?.avg_pages_discovered ?? 0)}</strong>
            </div>
            <div className="stat-card">
              <span className="stat-label">میانگین crawl</span>
              <strong>{Math.round(ch?.avg_pages_crawled ?? 0)}</strong>
            </div>
          </div>

          <section className="panel">
            <h3>تعداد رکوردها در DB</h3>
            <div className="table-counts-grid">
              {overview.table_counts.map((row) => (
                <div key={row.table} className="table-count-item">
                  <span className="mono">{row.table}</span>
                  <strong>{row.count.toLocaleString("fa-IR")}</strong>
                </div>
              ))}
            </div>
          </section>

          {overview.depth_distribution.length > 0 && (
            <section className="panel">
              <h3>توزیع عمق صفحات</h3>
              <div className="depth-bars">
                {overview.depth_distribution.map((row) => {
                  const max = Math.max(...overview.depth_distribution.map((d) => d.count), 1);
                  const pct = (row.count / max) * 100;
                  return (
                    <div key={row.depth} className="depth-bar-row">
                      <span className="depth-label">L{row.depth}</span>
                      <div className="depth-bar-track">
                        <div className="depth-bar-fill" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="depth-count">{row.count.toLocaleString("fa-IR")}</span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {overview.last_site_map_job.job_id && (
            <section className="panel">
              <h3>آخرین site-map job</h3>
              <dl className="detail-grid task-meta">
                <dt>job</dt>
                <dd className="mono">{overview.last_site_map_job.job_id}</dd>
                <dt>وضعیت</dt>
                <dd>{overview.last_site_map_job.status ?? "—"}</dd>
                <dt>کرawl</dt>
                <dd>{overview.last_site_map_job.pages_crawled}</dd>
                <dt>کشف</dt>
                <dd>{overview.last_site_map_job.pages_discovered}</dd>
                <dt>خطا</dt>
                <dd>{overview.last_site_map_job.pages_failed}</dd>
                <dt>شروع</dt>
                <dd>{fmtTime(overview.last_site_map_job.started_at)}</dd>
                <dt>پایان</dt>
                <dd>{fmtTime(overview.last_site_map_job.finished_at)}</dd>
              </dl>
            </section>
          )}
        </>
      )}

      <section className="panel">
        <h3>فیلترهای فعال ({filterCrawls.length})</h3>
        {filterCrawls.length === 0 ? (
          <p className="muted">هیچ فیلتر فعالی crawl نشده است.</p>
        ) : (
          <div className="table-scroll">
            <table className="stats-table">
              <thead>
                <tr>
                  <th>فیلتر</th>
                  <th>بخش</th>
                  <th>searches</th>
                  <th>آخرین crawl</th>
                  <th>checkpoint</th>
                  <th>job</th>
                  <th>وضعیت</th>
                </tr>
              </thead>
              <tbody>
                {filterCrawls.map((row) => (
                  <tr key={row.fingerprint}>
                    <td>
                      {[row.brand, row.model].filter(Boolean).join(" ") || "—"}
                      {row.min_year ? ` ≥${row.min_year}` : ""}
                      {row.max_price ? ` ≤${row.max_price}` : ""}
                      {row.location ? ` · ${row.location}` : ""}
                    </td>
                    <td>{row.section_key}</td>
                    <td>{row.enabled_search_count}</td>
                    <td>{fmtTime(row.last_crawl_at)}</td>
                    <td className="mono">{row.last_seen_bama_id?.slice(0, 12) ?? "—"}</td>
                    <td className="mono">{row.active_job_id?.slice(0, 10) ?? row.last_job_id?.slice(0, 10) ?? "—"}</td>
                    <td>{row.active_job_status ?? "idle"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-head-row">
          <h3>کشف فیلترها ({filteredSearches.length}/{searches.length})</h3>
          <div className="filter-chips">
            {(["all", "low_yield", "enabled", "disabled"] as SearchFilter[]).map((f) => (
              <button
                key={f}
                type="button"
                className={`section-chip ${searchFilter === f ? "active" : ""}`}
                onClick={() => setSearchFilter(f)}
              >
                {f === "all" ? "همه" : f === "low_yield" ? "کم‌بازده" : f === "enabled" ? "فعال" : "غیرفعال"}
              </button>
            ))}
          </div>
        </div>
        {filteredSearches.length === 0 ? (
          <p className="muted">فیلتری برای نمایش نیست.</p>
        ) : (
          <div className="table-scroll">
            <table className="stats-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>نام / فیلتر</th>
                  <th>بخش</th>
                  <th>فعال</th>
                  <th>bootstrap</th>
                  <th>URL</th>
                  <th>pages</th>
                  <th>ads</th>
                  <th>match</th>
                  <th>نرخ</th>
                  <th>کم‌بازده</th>
                </tr>
              </thead>
              <tbody>
                {filteredSearches.map((row) => (
                  <tr key={row.search_id} className={row.low_yield ? "row-warning" : ""}>
                    <td>{row.search_id}</td>
                    <td>{row.name || [row.brand, row.model].filter(Boolean).join(" ") || "—"}</td>
                    <td>{row.section_key}</td>
                    <td>{row.enabled ? "✓" : "—"}</td>
                    <td>{fmtTime(row.bootstrapped_at)}</td>
                    <td className="mono">{row.listing_url ?? "—"}</td>
                    <td>{row.pages_crawled}</td>
                    <td>{row.ads_found}</td>
                    <td>{row.matching_count}</td>
                    <td>{fmtPct(row.match_rate)}</td>
                    <td>{row.low_yield ? "بله" : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {overview && overview.site_coverage.length > 0 && (
        <section className="panel">
          <h3>پوشش سایت ({overview.site_coverage.length} گروه)</h3>
          <div className="table-scroll">
            <table className="stats-table">
              <thead>
                <tr>
                  <th>بخش</th>
                  <th>نوع صفحه</th>
                  <th>تعداد</th>
                </tr>
              </thead>
              <tbody>
                {overview.site_coverage.map((row, i) => (
                  <tr key={`${row.section}-${row.page_type}-${i}`}>
                    <td>{row.section}</td>
                    <td>{row.page_type}</td>
                    <td>{row.count.toLocaleString("fa-IR")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
