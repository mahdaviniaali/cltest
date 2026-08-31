import type { SiteMapJob } from "../../api/inspector";

interface Props {
  job: SiteMapJob | null;
  loading: boolean;
  currentLevelPages?: number;
  sectionsAtLevel?: string[];
  onStart: (maxPages: number, maxDepth: number) => void;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
}

export default function SiteMapControl({
  job,
  loading,
  currentLevelPages,
  sectionsAtLevel,
  onStart,
  onPause,
  onResume,
  onCancel,
}: Props) {
  const running = job?.status === "running";
  const paused = job?.status === "paused";

  return (
    <div className="inspector-control">
      <div className="inspector-control-actions">
        <button disabled={loading || running} onClick={() => onStart(500, 6)}>
          اکتشاف ۵۰۰ صفحه جدید
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
      {job && (
        <div className="inspector-stats">
          <span>وضعیت: {job.status}</span>
          <span>سطح: {job.current_depth}</span>
          <span>کرawl: {job.pages_crawled}</span>
          <span>کشف: {job.pages_discovered}</span>
          <span>خطا: {job.pages_failed}</span>
          {currentLevelPages !== undefined && currentLevelPages > 0 && (
            <span>صفحات سطح: {currentLevelPages}</span>
          )}
          {sectionsAtLevel && sectionsAtLevel.length > 0 && (
            <span>بخش‌ها: {sectionsAtLevel.join(", ")}</span>
          )}
        </div>
      )}
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
