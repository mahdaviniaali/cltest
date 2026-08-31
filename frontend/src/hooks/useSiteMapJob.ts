import { useCallback, useEffect, useRef, useState } from "react";
import { inspectorApi, type CrawlEvent, type SiteMapJob } from "../api/inspector";

const LIVE_STATUSES = new Set(["running", "paused", "pending"]);

function isLive(job: SiteMapJob | null | undefined): boolean {
  return Boolean(job && LIVE_STATUSES.has(job.status));
}

export function useSiteMapJob(pollMs = 2000) {
  const [jobs, setJobs] = useState<SiteMapJob[]>([]);
  const [job, setJob] = useState<SiteMapJob | null>(null);
  const [events, setEvents] = useState<CrawlEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const sinceIdRef = useRef(0);
  const selectedJobIdRef = useRef<string | null>(null);
  const userPinnedRef = useRef(false);

  const refreshJob = useCallback(async (jobId: string) => {
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

  const loadJobs = useCallback(async () => {
    const jobsList = await inspectorApi.listJobs();
    setJobs(jobsList);
    const active = jobsList.find((j) => isLive(j));
    const selectedId = selectedJobIdRef.current;

    if (userPinnedRef.current && selectedId) {
      const selected = jobsList.find((j) => j.job_id === selectedId);
      if (selected) {
        setJob(selected);
        return selected;
      }
      userPinnedRef.current = false;
    }

    if (active) {
      if (selectedJobIdRef.current !== active.job_id) {
        sinceIdRef.current = 0;
        setEvents([]);
      }
      selectedJobIdRef.current = active.job_id;
      setJob(active);
      return active;
    }

    if (selectedId) {
      const selected = jobsList.find((j) => j.job_id === selectedId);
      if (selected) {
        setJob(selected);
        return selected;
      }
    }

    const latest = jobsList[0] ?? null;
    selectedJobIdRef.current = latest?.job_id ?? null;
    setJob(latest);
    return latest;
  }, []);

  const selectJob = useCallback(
    async (jobId: string) => {
      userPinnedRef.current = true;
      selectedJobIdRef.current = jobId;
      sinceIdRef.current = 0;
      setEvents([]);
      setError("");
      const data = await inspectorApi.getJob(jobId);
      setJob(data);
      await pollEvents(jobId);
      return data;
    },
    [pollEvents],
  );

  useEffect(() => {
    void loadJobs().catch((err: Error) => setError(err.message));
    const id = window.setInterval(() => {
      void loadJobs().catch(() => undefined);
    }, pollMs);
    return () => window.clearInterval(id);
  }, [loadJobs, pollMs]);

  useEffect(() => {
    if (!job?.job_id || !isLive(job)) return;
    const jobId = job.job_id;
    const tick = () => {
      void refreshJob(jobId).catch(() => undefined);
      void pollEvents(jobId).catch(() => undefined);
    };
    tick();
    const id = window.setInterval(tick, pollMs);
    return () => window.clearInterval(id);
  }, [job?.job_id, job?.status, pollMs, refreshJob, pollEvents]);

  async function start(maxPages?: number, maxDepth?: number) {
    setLoading(true);
    setError("");
    try {
      userPinnedRef.current = false;
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
