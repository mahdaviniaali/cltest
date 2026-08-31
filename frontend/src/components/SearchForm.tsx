import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  const [catalogLoading, setCatalogLoading] = useState(false);
  const harvestedRef = useRef(false);

  useEffect(() => {
    void taxonomyApi
      .sections()
      .then(setSections)
      .catch(() => setTaxonomyError("بارگذاری بخش‌ها ناموفق بود"));
  }, []);

  useEffect(() => {
    const section = form.section_key || "car";
    let cancelled = false;
    void (async () => {
      try {
        let rows = await taxonomyApi.brands(section);
        if (!cancelled && rows.length === 0 && !harvestedRef.current) {
          setCatalogLoading(true);
          await taxonomyApi.harvest();
          harvestedRef.current = true;
          rows = await taxonomyApi.brands(section);
        }
        if (!cancelled) setBrands(rows);
      } catch {
        if (!cancelled) {
          setBrands([]);
          setTaxonomyError("بارگذاری برندها ناموفق بود — می‌توانید خودتان بنویسید");
        }
      } finally {
        if (!cancelled) setCatalogLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [form.section_key]);

  useEffect(() => {
    const section = form.section_key || "car";
    const matched = matchTerm(brands, form.brand ?? "");
    const brandId = form.brand_term_id ?? matched?.id;
    if (!brandId) {
      setModels([]);
      return;
    }
    void taxonomyApi
      .models(section, brandId)
      .then(setModels)
      .catch(() => setModels([]));
  }, [form.section_key, form.brand, form.brand_term_id, brands]);

  useEffect(() => {
    const brandTerm = matchTerm(brands, form.brand ?? "");
    const modelTerm = matchTerm(models, form.model ?? "");
    if (!brandTerm && !modelTerm) return;
    setForm((prev) => {
      const nextBrandId = brandTerm?.id ?? prev.brand_term_id;
      const nextModelId = modelTerm?.id ?? prev.model_term_id;
      if (prev.brand_term_id === nextBrandId && prev.model_term_id === nextModelId) return prev;
      return { ...prev, brand_term_id: nextBrandId, model_term_id: nextModelId };
    });
  }, [brands, models, form.brand, form.model]);

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

  function onBrandInput(value: string) {
    const term = matchTerm(brands, value);
    setForm((prev) => {
      const brandChanged = term?.id !== prev.brand_term_id;
      return {
        ...prev,
        brand: value,
        brand_term_id: term?.id,
        model: brandChanged ? "" : prev.model,
        model_term_id: brandChanged ? undefined : prev.model_term_id,
      };
    });
  }

  function onModelInput(value: string) {
    const term = matchTerm(models, value);
    setForm((prev) => ({
      ...prev,
      model: value,
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
            <input
              list="brand-suggestions"
              value={form.brand ?? ""}
              onChange={(e) => onBrandInput(e.target.value)}
              placeholder="تویوتا یا Toyota"
              autoComplete="off"
            />
            <datalist id="brand-suggestions">
              {brands.map((b) => (
                <option key={b.id} value={b.label} />
              ))}
            </datalist>
          </label>
          <label>
            مدل
            <input
              list="model-suggestions"
              value={form.model ?? ""}
              onChange={(e) => onModelInput(e.target.value)}
              placeholder="کمری یا Camry"
              autoComplete="off"
            />
            <datalist id="model-suggestions">
              {models.map((m) => (
                <option key={m.id} value={m.label} />
              ))}
            </datalist>
          </label>
        </div>
        <p className="muted">
          {catalogLoading
            ? "در حال دریافت برند و مدل از باما…"
            : "می‌توانید برند و مدل را خودتان بنویسید یا از پیشنهادها انتخاب کنید."}
        </p>
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

function matchTerm(terms: TaxonomyTerm[], value: string): TaxonomyTerm | undefined {
  const needle = value.trim().toLowerCase();
  if (!needle) return undefined;
  const spaced = needle.replace(/-/g, " ");
  const compactNeedle = needle.replace(/[\s-]+/g, "");
  return (
    terms.find((t) => t.label.toLowerCase() === needle || t.slug.toLowerCase() === needle) ??
    terms.find((t) => t.slug.replace(/-/g, " ").toLowerCase() === spaced) ??
    terms.find((t) => t.label.toLowerCase().split(/\s+/).some((token) => token === needle)) ??
    terms.find((t) => {
      if (compactNeedle.length < 2) return false;
      const compactLabel = t.label.toLowerCase().replace(/[\s-]+/g, "");
      const compactSlug = t.slug.toLowerCase().replace(/[\s-]+/g, "");
      if (compactLabel === compactNeedle || compactSlug === compactNeedle) return true;
      return compactNeedle.length >= 3 && (compactLabel.includes(compactNeedle) || compactSlug.includes(compactNeedle));
    })
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
