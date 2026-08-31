import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { Ad, DataPreview } from "../types";

function formatPrice(value: number | null) {
  if (value == null) return "—";
  return new Intl.NumberFormat("fa-IR").format(value);
}

function formatDate(value: string | null) {
  if (!value) return "نامشخص";
  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

interface Props {
  preview: DataPreview | null;
  loading: boolean;
  onRefresh: () => void;
  refreshing: boolean;
  searchId?: number;
}

export default function AdPreviewPanel({
  preview,
  loading,
  onRefresh,
  refreshing,
  searchId,
}: Props) {
  const showHandoffHint = preview?.bootstrapped && preview.cache_sufficient;

  return (
    <section className="panel preview-panel">
      <div className="preview-header">
        <div>
          <h3>پیش‌نمایش داده‌های موجود</h3>
          <p className="muted">
            آخرین بروزرسانی این فیلتر: {formatDate(preview?.last_updated_at ?? null)}
          </p>
          {showHandoffHint && (
            <p className="muted">بروزرسانی بعدی از crawl دوره‌ای انجام می‌شود.</p>
          )}
        </div>
        <button type="button" onClick={onRefresh} disabled={refreshing || preview?.is_refreshing}>
          {refreshing || preview?.is_refreshing
            ? "در حال بروزرسانی..."
            : searchId
              ? "بروزرسانی داده‌ها"
              : "بروزرسانی سراسری"}
        </button>
      </div>

      {(preview?.is_refreshing || refreshing) && (
        <p className="refresh-banner">
          در حال جستجو در bama.ir
          {preview && (preview.pages_crawled || preview.ads_found)
            ? ` — صفحه ${preview.pages_crawled ?? 0}، ${preview.ads_found ?? 0} آگهی پیدا شد` +
              (preview.ads_new ? ` (${preview.ads_new} جدید)` : "")
            : " و بروزرسانی cache..."}
        </p>
      )}

      {loading && <p className="muted">در حال بارگذاری پیش‌نمایش...</p>}

      {!loading && preview && (
        <>
          <p className="preview-count">
            {preview.total_count} آگهی مطابق با معیارهای شما در cache موجود است
          </p>
          {preview.total_count === 0 ? (
            <p className="muted">
              {preview.is_refreshing
                ? "در حال جستجو برای یافتن آگهی..."
                : "هنوز آگهی‌ای با این مشخصات ذخیره نشده — با ذخیره فیلتر، جستجو آغاز می‌شود."}
            </p>
          ) : (
            <ul className="ad-list">
              {preview.ads.map((ad) => (
                <AdCard key={ad.bama_id} ad={ad} />
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}

function AdCard({ ad }: { ad: Ad }) {
  return (
    <li className="ad-card">
      <div>
        <strong>{ad.title}</strong>
        <p className="muted ad-meta">
          {[ad.brand, ad.model, ad.year ? `سال ${ad.year}` : null, ad.location]
            .filter(Boolean)
            .join(" · ")}
        </p>
        <p className="ad-price">{formatPrice(ad.price)} تومان</p>
      </div>
      <a href={ad.url} target="_blank" rel="noreferrer">
        مشاهده
      </a>
    </li>
  );
}

export function useSearchRefresh(searchId: number | undefined, onComplete: () => void) {
  const [refreshing, setRefreshing] = useState(false);

  const pollUntilDone = useCallback(async () => {
    for (let i = 0; i < 60; i++) {
      await new Promise((r) => setTimeout(r, 5000));
      if (!searchId) break;
      const preview = await api.getSearchResults(searchId);
      if (!preview.is_refreshing) {
        setRefreshing(false);
        onComplete();
        return;
      }
    }
    setRefreshing(false);
  }, [onComplete, searchId]);

  const triggerRefresh = useCallback(async () => {
    if (!searchId) return;
    setRefreshing(true);
    await api.refreshSearch(searchId);
    void pollUntilDone();
  }, [pollUntilDone, searchId]);

  return { refreshing, triggerRefresh };
}

export function useDataRefresh(onComplete: () => void) {
  const [refreshing, setRefreshing] = useState(false);

  const pollUntilDone = useCallback(async () => {
    for (let i = 0; i < 60; i++) {
      await new Promise((r) => setTimeout(r, 5000));
      const status = await api.getDataStatus();
      if (!status.is_refreshing) {
        setRefreshing(false);
        onComplete();
        return;
      }
    }
    setRefreshing(false);
  }, [onComplete]);

  const triggerRefresh = useCallback(async () => {
    setRefreshing(true);
    await api.refreshData();
    void pollUntilDone();
  }, [pollUntilDone]);

  return { refreshing, triggerRefresh };
}

export function useLivePreview(filter: {
  brand?: string;
  model?: string;
  min_year?: number;
  max_price?: number;
  max_mileage?: number;
  location?: string;
}) {
  const [preview, setPreview] = useState<DataPreview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const hasCriteria = Object.values(filter).some((v) => v !== undefined && v !== "");
    if (!hasCriteria) {
      setPreview(null);
      return;
    }

    const timer = setTimeout(() => {
      setLoading(true);
      api
        .previewAds(filter)
        .then(setPreview)
        .catch(() => setPreview(null))
        .finally(() => setLoading(false));
    }, 400);

    return () => clearTimeout(timer);
  }, [filter.brand, filter.model, filter.min_year, filter.max_price, filter.max_mileage, filter.location]);

  return { preview, loading, setPreview };
}

export async function pollSearchBootstrap(
  searchId: number,
  jobId: string | null | undefined,
  onTick: () => void,
): Promise<void> {
  for (let i = 0; i < 60; i++) {
    await new Promise((r) => setTimeout(r, 3000));
    onTick();
    const preview = await api.getSearchResults(searchId);
    if (!preview.is_refreshing && preview.total_count > 0) return;
    if (jobId) {
      try {
        const job = await api.getCrawlJob(jobId);
        if (job.status === "completed" || job.status === "failed") return;
      } catch {
        /* job may not exist yet */
      }
    }
  }
}
