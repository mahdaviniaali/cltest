import { useCallback, useEffect, useRef, useState } from "react";
import { inspectorApi, type CrawlEvent, type SiteMapJob } from "../api/inspector";

export function useSiteMapJob(pollMs = 2000) {
  const [jobs, setJobs] = useState<SiteMapJob[]>([]);
  const [job, setJob] = useState<SiteMapJob | null>(null);
  const [events, setEvents] = useState<CrawlEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const sinceIdRef = useRef(0);
  const selectedJobIdRef = useRef<string | null>(null);

  const refreshJob = useCallback(async (jobId: string) => {
    const data = await inspectorApi.getJob(jobId);
    setJob(data);
    return data;
  }, []);

  const loadJobs = useCallback(async () => {
    const jobsList = await inspectorApi.listJobs();
    setJobs(jobsList);
    const selectedId = selectedJobIdRef.current;
    if (selectedId && jobsList.some((j) => j.job_id === selectedId)) {
      const selected = jobsList.find((j) => j.job_id === selectedId)!;
      setJob(selected);
      return selected;
    }
    const active = jobsList.find((j) => j.status === "running" || j.status === "paused");
    const latest = active ?? jobsList[0] ?? null;
    if (latest) {
      selectedJobIdRef.current = latest.job_id;
    }
    setJob(latest);
    return latest;
  }, []);

  const selectJob = useCallback(async (jobId: string) => {
    selectedJobIdRef.current = jobId;
    sinceIdRef.current = 0;
    setEvents([]);
    setError("");
    const data = await inspectorApi.getJob(jobId);
    setJob(data);
    return data;
  }, []);

  const pollEvents = useCallback(async (jobId: string) => {
    const batch = await inspectorApi.listEvents(jobId, sinceIdRef.current);
    if (batch.length > 0) {
      sinceIdRef.current = batch[batch.length - 1].id;
      setEvents((prev) => [...prev, ...batch].slice(-500));
    }
  }, []);

  useEffect(() => {
    void loadJobs().catch((err: Error) => setError(err.message));
  }, [loadJobs]);

  useEffect(() => {
    if (!job?.job_id) return;
    const tick = () => {
      void refreshJob(job.job_id).catch(() => undefined);
      void pollEvents(job.job_id).catch(() => undefined);
    };
    tick();
    const id = window.setInterval(tick, pollMs);
    return () => window.clearInterval(id);
  }, [job?.job_id, pollMs, refreshJob, pollEvents]);

  async function start(maxPages?: number, maxDepth?: number) {
    setLoading(true);
    setError("");
    try {
      sinceIdRef.current = 0;
      setEvents([]);
      const created = await inspectorApi.startSiteMap(maxPages, maxDepth);
      selectedJobIdRef.current = created.job_id;
      setJob(created);
      await loadJobs();
      return created;
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطا");
      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function pause() {
    if (!job) return;
    setJob(await inspectorApi.pauseJob(job.job_id));
  }

  async function resume() {
    if (!job) return;
    setJob(await inspectorApi.resumeJob(job.job_id));
  }

  async function cancel() {
    if (!job) return;
    setJob(await inspectorApi.cancelJob(job.job_id));
  }

  return { jobs, job, events, loading, error, start, pause, resume, cancel, loadJobs, selectJob };
}
