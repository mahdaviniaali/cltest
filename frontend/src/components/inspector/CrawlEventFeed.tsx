import type { CrawlEvent } from "../../api/inspector";
import ExternalLink from "./ExternalLink";

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

function eventUrl(payload: Record<string, unknown>): string | null {
  const url = payload.url;
  return typeof url === "string" && url.startsWith("http") ? url : null;
}

function eventMeta(payload: Record<string, unknown>): string {
  const parts: string[] = [];
  if (payload.depth != null) parts.push(`عمق ${payload.depth}`);
  if (typeof payload.section === "string" && payload.section) parts.push(payload.section);
  if (typeof payload.page_type === "string" && payload.page_type) parts.push(payload.page_type);
  if (typeof payload.reason === "string" && payload.reason) parts.push(payload.reason);
  return parts.join(" · ");
}

export default function CrawlEventFeed({ events }: Props) {
  if (events.length === 0) {
    return <p className="muted">هنوز رویدادی ثبت نشده.</p>;
  }
  return (
    <div className="event-feed">
      {[...events].reverse().map((event) => {
        const url = eventUrl(event.payload);
        const meta = eventMeta(event.payload);
        return (
          <div key={event.id} className={`event-row event-${event.event_type}`}>
            <div className="event-head">
              <strong>{LABELS[event.event_type] || event.event_type}</strong>
              <time>{new Date(event.created_at).toLocaleTimeString("fa-IR")}</time>
            </div>
            {url && (
              <p className="event-url">
                <ExternalLink href={url}>{url}</ExternalLink>
              </p>
            )}
            {meta && <p className="event-meta muted">{meta}</p>}
          </div>
        );
      })}
    </div>
  );
}
