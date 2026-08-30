import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { Search, SearchInput } from "../types";
import AdPreviewPanel, { useDataRefresh, useLivePreview } from "./AdPreviewPanel";

interface Props {
  initial?: Search;
  onSubmit: (data: SearchInput) => Promise<void>;
  onCancel: () => void;
}

const emptyForm: SearchInput = {
  name: "",
  brand: "",
  model: "",
  min_year: undefined,
  max_price: undefined,
  max_mileage: undefined,
  location: "",
  enabled: true,
};

export default function SearchForm({ initial, onSubmit, onCancel }: Props) {
  const [form, setForm] = useState<SearchInput>(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initial) {
      setForm({
        name: initial.name ?? "",
        brand: initial.brand ?? "",
        model: initial.model ?? "",
        min_year: initial.min_year ?? undefined,
        max_price: initial.max_price ?? undefined,
        max_mileage: initial.max_mileage ?? undefined,
        location: initial.location ?? "",
        enabled: initial.enabled,
      });
    } else {
      setForm(emptyForm);
    }
  }, [initial]);

  const filter = useMemo(
    () => ({
      brand: form.brand || undefined,
      model: form.model || undefined,
      min_year: form.min_year,
      max_price: form.max_price,
      max_mileage: form.max_mileage,
      location: form.location || undefined,
    }),
    [form.brand, form.model, form.min_year, form.max_price, form.max_mileage, form.location],
  );

  const { preview, loading, setPreview } = useLivePreview(filter);
  const reloadPreview = useCallback(() => {
    const hasCriteria = Object.values(filter).some((v) => v !== undefined && v !== "");
    if (!hasCriteria) return;
    setLoadingPreview(true);
    api
      .previewAds({ ...filter, limit: 20 })
      .then(setPreview)
      .finally(() => setLoadingPreview(false));
  }, [filter, setPreview]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const { refreshing, triggerRefresh } = useDataRefresh(reloadPreview);

  function setField<K extends keyof SearchInput>(key: K, value: SearchInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await onSubmit({
        ...form,
        name: form.name || undefined,
        brand: form.brand || undefined,
        model: form.model || undefined,
        location: form.location || undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطا در ذخیره");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <form className="form panel" onSubmit={handleSubmit}>
        <h2>{initial ? "ویرایش فیلتر" : "فیلتر جدید"}</h2>
        <label>
          نام فیلتر (اختیاری)
          <input value={form.name ?? ""} onChange={(e) => setField("name", e.target.value)} />
        </label>
        <div className="grid-2">
          <label>
            برند
            <input value={form.brand ?? ""} onChange={(e) => setField("brand", e.target.value)} placeholder="تویوتا" />
          </label>
          <label>
            مدل
            <input value={form.model ?? ""} onChange={(e) => setField("model", e.target.value)} placeholder="کمری" />
          </label>
        </div>
        <div className="grid-2">
          <label>
            حداقل سال
            <input
              type="number"
              value={form.min_year ?? ""}
              onChange={(e) => setField("min_year", e.target.value ? Number(e.target.value) : undefined)}
              placeholder="1400"
            />
          </label>
          <label>
            حداکثر قیمت (تومان)
            <input
              type="number"
              value={form.max_price ?? ""}
              onChange={(e) => setField("max_price", e.target.value ? Number(e.target.value) : undefined)}
              placeholder="3000000000"
            />
          </label>
        </div>
        <div className="grid-2">
          <label>
            حداکثر کارکرد (km)
            <input
              type="number"
              value={form.max_mileage ?? ""}
              onChange={(e) => setField("max_mileage", e.target.value ? Number(e.target.value) : undefined)}
              placeholder="100000"
            />
          </label>
          <label>
            موقعیت
            <input value={form.location ?? ""} onChange={(e) => setField("location", e.target.value)} placeholder="تهران" />
          </label>
        </div>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={form.enabled ?? true}
            onChange={(e) => setField("enabled", e.target.checked)}
          />
          فیلتر فعال باشد
        </label>
        {error && <p className="error">{error}</p>}
        <div className="actions">
          <button type="button" className="secondary" onClick={onCancel}>
            انصراف
          </button>
          <button type="submit" disabled={submitting}>
            {submitting ? "در حال ذخیره..." : "ذخیره"}
          </button>
        </div>
      </form>

      <AdPreviewPanel
        preview={preview}
        loading={loading || loadingPreview}
        onRefresh={() => void triggerRefresh()}
        refreshing={refreshing}
      />
    </>
  );
}

function formatPrice(value: number | null) {
  if (value == null) return "—";
  return new Intl.NumberFormat("fa-IR").format(value);
}

export function SearchSummary({ search }: { search: Search }) {
  const parts = [
    search.name,
    [search.brand, search.model].filter(Boolean).join(" "),
    search.min_year ? `سال ≥ ${search.min_year}` : null,
    search.max_price ? `قیمت ≤ ${formatPrice(search.max_price)}` : null,
    search.max_mileage ? `کارکرد ≤ ${formatPrice(search.max_mileage)} km` : null,
    search.location,
  ].filter(Boolean);

  return <p className="search-summary">{parts.join(" · ") || "بدون معیار"}</p>;
}
