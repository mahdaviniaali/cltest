import type { CrawlEvent } from "../../api/inspector";

interface Props {
  events: CrawlEvent[];
}

const LABELS: Record<string, string> = {
  job_started: "شروع job",
  page_fetched: "صفحه دریافت شد",
  page_failed: "خطا در صفحه",
  page_skipped: "رد شد",
  section_detected: "بخش شناسایی شد",
  level_completed: "سطح تکمیل شد",
  job_paused: "متوقف شد",
  job_completed: "تکمیل شد",
};

export default function CrawlEventFeed({ events }: Props) {
  if (events.length === 0) {
    return <p className="muted">هنوز رویدادی ثبت نشده.</p>;
  }
  return (
    <div className="event-feed">
      {[...events].reverse().map((event) => (
        <div key={event.id} className={`event-row event-${event.event_type}`}>
          <div className="event-head">
            <strong>{LABELS[event.event_type] || event.event_type}</strong>
            <time>{new Date(event.created_at).toLocaleTimeString("fa-IR")}</time>
          </div>
          <pre>{JSON.stringify(event.payload, null, 0).slice(0, 200)}</pre>
        </div>
      ))}
    </div>
  );
}
