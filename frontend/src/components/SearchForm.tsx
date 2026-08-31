import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { taxonomyApi, type TaxonomySection, type TaxonomyTerm } from "../api/taxonomy";
import type { Search, SearchInput, SearchUpdateInput } from "../types";
import AdPreviewPanel, { useDataRefresh, useLivePreview } from "./AdPreviewPanel";

interface Props {
  initial?: Search;
  onSubmit: (data: SearchInput | SearchUpdateInput) => Promise<void>;
  onCancel: () => void;
  isEdit?: boolean;
}

const emptyForm: SearchInput = {
  name: "",
  section_key: "car",
  brand: "",
  model: "",
  brand_term_id: undefined,
  model_term_id: undefined,
  min_year: undefined,
  max_price: undefined,
  max_mileage: undefined,
  location: "",
  enabled: true,
};

export default function SearchForm({ initial, onSubmit, onCancel, isEdit = false }: Props) {
  const [form, setForm] = useState<SearchInput>(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [sections, setSections] = useState<TaxonomySection[]>([]);
  const [brands, setBrands] = useState<TaxonomyTerm[]>([]);
  const [models, setModels] = useState<TaxonomyTerm[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [taxonomyError, setTaxonomyError] = useState("");

  useEffect(() => {
    void taxonomyApi
      .sections()
      .then(setSections)
      .catch(() => setTaxonomyError("بارگذاری بخش‌ها ناموفق بود"));
  }, []);

  useEffect(() => {
    const section = form.section_key || "car";
    void taxonomyApi
      .brands(section)
      .then(setBrands)
      .catch(() => setBrands([]));
  }, [form.section_key]);

  useEffect(() => {
    const section = form.section_key || "car";
    if (!form.brand_term_id) {
      setModels([]);
      return;
    }
    void taxonomyApi
      .models(section, form.brand_term_id)
      .then(setModels)
      .catch(() => setModels([]));
  }, [form.section_key, form.brand_term_id]);

  useEffect(() => {
    const section = form.section_key || "car";
    void taxonomyApi
      .cities(section)
      .then((rows) => setCities(rows.map((c) => c.label)))
      .catch(() => setCities([]));
  }, [form.section_key]);

  useEffect(() => {
    if (initial) {
      setForm({
        name: initial.name ?? "",
        section_key: initial.section_key ?? "car",
        brand: initial.brand ?? "",
        model: initial.model ?? "",
        brand_term_id: initial.brand_term_id ?? undefined,
        model_term_id: initial.model_term_id ?? undefined,
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

  function onSectionChange(sectionKey: string) {
    setForm((prev) => ({
      ...prev,
      section_key: sectionKey,
      brand: "",
      model: "",
      brand_term_id: undefined,
      model_term_id: undefined,
    }));
  }

  function onBrandChange(brandId: string) {
    if (!brandId) {
      setForm((prev) => ({
        ...prev,
        brand: "",
        model: "",
        brand_term_id: undefined,
        model_term_id: undefined,
      }));
      return;
    }
    const term = brands.find((b) => String(b.id) === brandId);
    setForm((prev) => ({
      ...prev,
      brand: term?.label ?? "",
      brand_term_id: term?.id,
      model: "",
      model_term_id: undefined,
    }));
  }

  function onModelChange(modelId: string) {
    if (!modelId) {
      setForm((prev) => ({ ...prev, model: "", model_term_id: undefined }));
      return;
    }
    const term = models.find((m) => String(m.id) === modelId);
    setForm((prev) => ({
      ...prev,
      model: term?.label ?? "",
      model_term_id: term?.id,
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      if (isEdit) {
        await onSubmit({
          name: form.name?.trim() ? form.name.trim() : null,
          section_key: form.section_key ?? "car",
          brand: form.brand?.trim() ? form.brand.trim() : null,
          model: form.model?.trim() ? form.model.trim() : null,
          brand_term_id: form.brand_term_id ?? null,
          model_term_id: form.model_term_id ?? null,
          min_year: form.min_year ?? null,
          max_price: form.max_price ?? null,
          max_mileage: form.max_mileage ?? null,
          location: form.location?.trim() ? form.location.trim() : null,
          enabled: form.enabled,
        });
      } else {
        await onSubmit({
          ...form,
          name: form.name || undefined,
          section_key: form.section_key || "car",
          brand: form.brand || undefined,
          model: form.model || undefined,
          location: form.location || undefined,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطا در ذخیره");
    } finally {
      setSubmitting(false);
    }
  }

  const sectionOptions =
    sections.length > 0
      ? sections
      : [
          { section_key: "car", label: "خودرو", brand_count: 0, model_count: 0 },
          { section_key: "motorcycle", label: "موتورسیکلت", brand_count: 0, model_count: 0 },
          { section_key: "truck", label: "وانت و کامیون", brand_count: 0, model_count: 0 },
        ];

  return (
    <>
      <form className="form panel" onSubmit={handleSubmit}>
        <h2>{initial ? "ویرایش فیلتر" : "فیلتر جدید"}</h2>
        <label>
          نام فیلتر (اختیاری)
          <input value={form.name ?? ""} onChange={(e) => setField("name", e.target.value)} />
        </label>
        <label>
          بخش
          <select value={form.section_key ?? "car"} onChange={(e) => onSectionChange(e.target.value)}>
            {sectionOptions.map((s) => (
              <option key={s.section_key} value={s.section_key}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <div className="grid-2">
          <label>
            برند
            <select
              value={form.brand_term_id ? String(form.brand_term_id) : ""}
              onChange={(e) => onBrandChange(e.target.value)}
            >
              <option value="">— انتخاب برند —</option>
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            مدل
            <select
              value={form.model_term_id ? String(form.model_term_id) : ""}
              onChange={(e) => onModelChange(e.target.value)}
              disabled={!form.brand_term_id}
            >
              <option value="">— انتخاب مدل —</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {taxonomyError && <p className="muted">{taxonomyError}</p>}
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
            <input
              list="city-suggestions"
              value={form.location ?? ""}
              onChange={(e) => setField("location", e.target.value)}
              placeholder="تهران"
            />
            <datalist id="city-suggestions">
              {cities.map((city) => (
                <option key={city} value={city} />
              ))}
            </datalist>
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
