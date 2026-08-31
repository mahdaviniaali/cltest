import { useState } from "react";
import type { SiteMapJob } from "../../api/inspector";
import { fmtJobTime, jobIsInterrupted, jobStatusClass, jobStatusLabel } from "../../lib/jobStatus";

interface Props {
  job: SiteMapJob | null;
  jobs: SiteMapJob[];
  loading: boolean;
  currentLevelPages?: number;
  sectionsAtLevel?: string[];
  onStart: (maxPages: number, maxDepth: number) => void;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onSelectJob: (jobId: string) => void;
  onHarvest?: () => void;
  harvestLoading?: boolean;
}

export default function SiteMapControl({
  job,
  jobs,
  loading,
  currentLevelPages,
  sectionsAtLevel,
  onStart,
  onPause,
  onResume,
  onCancel,
  onSelectJob,
  onHarvest,
  harvestLoading = false,
}: Props) {
  const [maxPages, setMaxPages] = useState(500);
  const [maxDepth, setMaxDepth] = useState(6);
  const running = job?.status === "running";
  const paused = job?.status === "paused";

  return (
    <div className="inspector-control">
      <div className="inspector-control-row">
        <div className="inspector-control-actions">
          <label className="control-field">
            <span>حداکثر صفحات</span>
            <input
              type="number"
              min={1}
              max={50000}
              value={maxPages}
              disabled={loading || running}
              onChange={(e) => setMaxPages(Number(e.target.value) || 500)}
            />
          </label>
          <label className="control-field">
            <span>عمق</span>
            <input
              type="number"
              min={1}
              max={20}
              value={maxDepth}
              disabled={loading || running}
              onChange={(e) => setMaxDepth(Number(e.target.value) || 6)}
            />
          </label>
          <button disabled={loading || running} onClick={() => onStart(maxPages, maxDepth)}>
            {loading ? "در حال شروع…" : "شروع site-map crawl"}
          </button>
          <button
            className="secondary"
            disabled={loading || running || harvestLoading || !onHarvest}
            onClick={() => onHarvest?.()}
          >
            {harvestLoading ? "در حال دریافت برند و مدل…" : "کشف همه برند و مدل"}
          </button>
          <button className="secondary" disabled={!running} onClick={onPause}>
            توقف
          </button>
          <button className="secondary" disabled={!paused} onClick={onResume}>
            ادامه
          </button>
          <button className="danger" disabled={!running && !paused} onClick={onCancel}>
            لغو
          </button>
        </div>

        {jobs.length > 0 && (
          <label className="control-field job-select-field">
            <span>انتخاب job</span>
            <select
              value={job?.job_id ?? ""}
              onChange={(e) => e.target.value && onSelectJob(e.target.value)}
            >
              {jobs.map((j) => (
                <option key={j.job_id} value={j.job_id}>
                  {j.job_id.slice(0, 8)}… · {jobStatusLabel(j)} · {j.pages_crawled}/{j.pages_discovered}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {job && (
        <div className="inspector-stats">
          <span>
            وضعیت: <strong className={`status-pill ${jobStatusClass(job)}`}>{jobStatusLabel(job)}</strong>
          </span>
          <span className="mono">ID: {job.job_id.slice(0, 12)}…</span>
          <span>سطح: {job.current_depth}</span>
          <span>کرawl: {job.pages_crawled}</span>
          <span>کشف: {job.pages_discovered}</span>
          <span>خطا: {job.pages_failed}</span>
          <span>شروع: {fmtJobTime(job.started_at)}</span>
          {job.finished_at && <span>پایان: {fmtJobTime(job.finished_at)}</span>}
          {currentLevelPages !== undefined && currentLevelPages > 0 && (
            <span>صفحات سطح: {currentLevelPages}</span>
          )}
          {sectionsAtLevel && sectionsAtLevel.length > 0 && (
            <span>بخش‌ها: {sectionsAtLevel.join(", ")}</span>
          )}
        </div>
      )}
      {job && jobIsInterrupted(job) && (
        <p className="muted job-error">
          این crawl قطع شد؛ {job.pages_crawled} صفحه در نقشه ذخیره شده
          {job.error ? ` (${job.error})` : "."}
        </p>
      )}
      {job?.error && !jobIsInterrupted(job) && <p className="error job-error">{job.error}</p>}
      {job && job.pages_discovered > 0 && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{
              width: `${Math.min(100, (job.pages_crawled / Math.max(job.pages_discovered, 1)) * 100)}%`,
            }}
          />
        </div>
      )}
    </div>
  );
}
