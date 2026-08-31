import { useCallback, useEffect, useState } from "react";
import {
  inspectorApi,
  type CrawlStatus,
  type FilterCrawlStat,
  type HealthReady,
  type SiteMapJob,
} from "../../api/inspector";
import { fmtJobTime, jobMessage, jobStatusClass, jobStatusLabel } from "../../lib/jobStatus";

function statusClassForFilter(status: string) {
  return jobStatusClass({ status, pages_crawled: 0 });
}

export default function InspectorTasksView() {
  const [health, setHealth] = useState<HealthReady | null>(null);
  const [crawlStatus, setCrawlStatus] = useState<CrawlStatus | null>(null);
  const [siteMapJobs, setSiteMapJobs] = useState<SiteMapJob[]>([]);
  const [filterCrawls, setFilterCrawls] = useState<FilterCrawlStat[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const results = await Promise.allSettled([
      inspectorApi.getHealthReady(),
      inspectorApi.getCrawlStatus(),
      inspectorApi.listJobs(),
      inspectorApi.getFilterCrawls(),
    ]);
    const nextErrors: string[] = [];
    if (results[0].status === "fulfilled") setHealth(results[0].value);
    else nextErrors.push(`health: ${results[0].reason instanceof Error ? results[0].reason.message : "خطا"}`);
    if (results[1].status === "fulfilled") setCrawlStatus(results[1].value);
    else nextErrors.push(`crawl: ${results[1].reason instanceof Error ? results[1].reason.message : "خطا"}`);
    if (results[2].status === "fulfilled") setSiteMapJobs(results[2].value);
    else nextErrors.push(`jobs: ${results[2].reason instanceof Error ? results[2].reason.message : "خطا"}`);
    if (results[3].status === "fulfilled") setFilterCrawls(results[3].value);
    else nextErrors.push(`filters: ${results[3].reason instanceof Error ? results[3].reason.message : "خطا"}`);
    setError(nextErrors.join(" · "));
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(id);
  }, [refresh]);

  const activeFilters = filterCrawls.filter(
    (f) => f.active_job_status === "running" || f.active_job_status === "pending" || f.active_job_status === "paused",
  );
  const activeSiteMap = siteMapJobs.filter(
    (j) => j.status === "running" || j.status === "pending" || j.status === "paused",
  );

  if (loading && !health) {
    return <p className="muted">در حال بارگذاری تسک‌ها…</p>;
  }

  return (
    <div className="inspector-tasks-panel">
      {error && <p className="error">{error}</p>}

      <section className="panel">
        <h3>وضعیت سیستم</h3>
        <div className="health-grid">
          <div className={`health-item ${health?.status === "ready" ? "ok" : "bad"}`}>
            <span>API</span>
            <strong>{health?.status === "ready" ? "آماده" : "مشکل"}</strong>
          </div>
          <div className={`health-item ${health?.checks.database === "ok" ? "ok" : "bad"}`}>
            <span>Database</span>
            <strong>{health?.checks.database === "ok" ? "OK" : health?.checks.database ?? "—"}</strong>
          </div>
          <div className={`health-item ${health?.checks.redis === "ok" ? "ok" : "bad"}`}>
            <span>Redis / Celery</span>
            <strong>{health?.checks.redis === "ok" ? "OK" : health?.checks.redis ?? "—"}</strong>
          </div>
          <div className={`health-item ${crawlStatus?.is_refreshing ? "running" : "ok"}`}>
            <span>Incremental crawl</span>
            <strong>{crawlStatus?.is_refreshing ? "در حال اجرا" : "idle"}</strong>
          </div>
        </div>
        {crawlStatus && (
          <dl className="detail-grid task-meta">
            <dt>آخرین crawl</dt>
            <dd>{fmtJobTime(crawlStatus.last_crawl_at)}</dd>
            <dt>checkpoint</dt>
            <dd className="mono">{crawlStatus.last_seen_bama_id?.slice(0, 16) ?? "—"}</dd>
            <dt>job آخر</dt>
            <dd className="mono">{crawlStatus.last_run_job_id?.slice(0, 12) ?? "—"}</dd>
          </dl>
        )}
      </section>

      <section className="panel">
        <h3>
          Site-map jobs فعال ({activeSiteMap.length})
          <button type="button" className="secondary refresh-btn" onClick={() => void refresh()}>
            بروزرسانی
          </button>
        </h3>
        {activeSiteMap.length === 0 ? (
          <p className="muted">هیچ site-map job در حال اجرا نیست.</p>
        ) : (
          <div className="table-scroll">
            <table className="stats-table">
              <thead>
                <tr>
                  <th>job</th>
                  <th>وضعیت</th>
                  <th>سطح</th>
                  <th>کرawl</th>
                  <th>کشف</th>
                  <th>خطا</th>
                  <th>شروع</th>
                </tr>
              </thead>
              <tbody>
                {activeSiteMap.map((job) => (
                  <tr key={job.job_id}>
                    <td className="mono">{job.job_id.slice(0, 10)}…</td>
                    <td>
                      <span className={`status-pill ${jobStatusClass(job)}`}>{jobStatusLabel(job)}</span>
                    </td>
                    <td>{job.current_depth}</td>
                    <td>{job.pages_crawled}</td>
                    <td>{job.pages_discovered}</td>
                    <td>{job.pages_failed}</td>
                    <td className="cell-time">{fmtJobTime(job.started_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <h3>فیلتر crawlهای فعال ({activeFilters.length})</h3>
        {activeFilters.length === 0 ? (
          <p className="muted">هیچ filter crawl در حال اجرا نیست.</p>
        ) : (
          <div className="table-scroll">
            <table className="stats-table">
              <thead>
                <tr>
                  <th>فیلتر</th>
                  <th>job</th>
                  <th>وضعیت</th>
                  <th>searches</th>
                  <th>آخرین crawl</th>
                </tr>
              </thead>
              <tbody>
                {activeFilters.map((row) => (
                  <tr key={row.fingerprint}>
                    <td>
                      {[row.brand, row.model].filter(Boolean).join(" ") || "—"}
                      {row.min_year ? ` ≥${row.min_year}` : ""}
                    </td>
                    <td className="mono">{row.active_job_id?.slice(0, 10) ?? "—"}</td>
                    <td>
                      <span className={`status-pill ${statusClassForFilter(row.active_job_status ?? "")}`}>
                        {jobStatusLabel({ status: row.active_job_status ?? "idle" })}
                      </span>
                    </td>
                    <td>{row.enabled_search_count}</td>
                    <td className="cell-time">{fmtJobTime(row.last_crawl_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <h3>تاریخچه site-map jobs ({siteMapJobs.length})</h3>
        {siteMapJobs.length === 0 ? (
          <p className="muted">هنوز site-map job ثبت نشده.</p>
        ) : (
          <div className="table-scroll">
            <table className="stats-table">
              <thead>
                <tr>
                  <th>job</th>
                  <th>وضعیت</th>
                  <th>کرawl</th>
                  <th>کشف</th>
                  <th>خطا</th>
                  <th>شروع</th>
                  <th>پایان</th>
                  <th>پیام</th>
                </tr>
              </thead>
              <tbody>
                {siteMapJobs.map((job) => (
                  <tr key={job.job_id}>
                    <td className="mono">{job.job_id.slice(0, 10)}…</td>
                    <td>
                      <span className={`status-pill ${jobStatusClass(job)}`}>{jobStatusLabel(job)}</span>
                    </td>
                    <td>{job.pages_crawled}</td>
                    <td>{job.pages_discovered}</td>
                    <td>{job.pages_failed}</td>
                    <td className="cell-time">{fmtJobTime(job.started_at)}</td>
                    <td className="cell-time">{fmtJobTime(job.finished_at)}</td>
                    <td className="cell-clip" title={job.error ?? ""}>
                      {jobMessage(job)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {crawlStatus?.latest_job && (
        <section className="panel">
          <h3>آخرین incremental job</h3>
          <dl className="detail-grid task-meta">
            <dt>job</dt>
            <dd className="mono">{crawlStatus.latest_job.id}</dd>
            <dt>نوع</dt>
            <dd>{crawlStatus.latest_job.job_type}</dd>
            <dt>وضعیت</dt>
            <dd>
              <span className={`status-pill ${jobStatusClass(crawlStatus.latest_job)}`}>
                {jobStatusLabel(crawlStatus.latest_job)}
              </span>
            </dd>
            <dt>صفحات</dt>
            <dd>{crawlStatus.latest_job.pages_crawled}</dd>
            <dt>آگهی</dt>
            <dd>
              {crawlStatus.latest_job.ads_found} ({crawlStatus.latest_job.ads_new} جدید)
            </dd>
            <dt>شروع</dt>
            <dd>{fmtJobTime(crawlStatus.latest_job.started_at)}</dd>
            <dt>پایان</dt>
            <dd>{fmtJobTime(crawlStatus.latest_job.finished_at)}</dd>
            {crawlStatus.latest_job.error && (
              <>
                <dt>خطا</dt>
                <dd className="mono">{crawlStatus.latest_job.error}</dd>
              </>
            )}
          </dl>
        </section>
      )}
    </div>
  );
}
