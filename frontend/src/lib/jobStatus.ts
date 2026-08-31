export type JobStatusFields = {
  status: string;
  pages_crawled?: number;
  error?: string | null;
};

const STATUS_LABELS: Record<string, string> = {
  running: "در حال اجرا",
  pending: "در صف",
  paused: "متوقف",
  completed: "تمام",
  failed: "ناموفق",
  cancelled: "لغو شده",
};

export function jobHasSavedPages(job: JobStatusFields): boolean {
  return (job.pages_crawled ?? 0) > 0;
}

export function jobIsInterrupted(job: JobStatusFields): boolean {
  return (job.status === "failed" || job.status === "cancelled") && jobHasSavedPages(job);
}

export function jobStatusLabel(job: JobStatusFields): string {
  if (jobIsInterrupted(job)) return "قطع شد";
  return STATUS_LABELS[job.status] ?? job.status;
}

export function jobStatusClass(job: JobStatusFields): string {
  if (jobIsInterrupted(job)) return "status-paused";
  if (job.status === "running" || job.status === "pending") return "status-running";
  if (job.status === "paused") return "status-paused";
  if (job.status === "failed") return "status-failed";
  if (job.status === "completed") return "status-completed";
  return "";
}

export function jobMessage(job: JobStatusFields): string {
  if (jobIsInterrupted(job)) {
    return `قطع شد — ${job.pages_crawled} صفحه ذخیره شد`;
  }
  return job.error?.trim() || "—";
}

export function fmtJobTime(value?: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("fa-IR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
